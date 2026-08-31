package com.kys.videomanager

import android.app.NotificationChannel
import android.app.NotificationManager
import android.app.PendingIntent
import android.app.Service
import android.content.Context
import android.content.Intent
import android.net.Uri
import android.os.Build
import android.os.IBinder
import android.provider.DocumentsContract
import android.text.format.Formatter
import android.util.Log
import androidx.core.app.NotificationCompat
import androidx.media3.common.Effect
import androidx.media3.common.MediaItem
import androidx.media3.common.MimeTypes
import androidx.media3.common.audio.AudioProcessor
import androidx.media3.effect.Presentation
import androidx.media3.transformer.Composition
import androidx.media3.transformer.DefaultEncoderFactory
import androidx.media3.transformer.EditedMediaItem
import androidx.media3.transformer.Effects
import androidx.media3.transformer.ExportException
import androidx.media3.transformer.ExportResult
import androidx.media3.transformer.ProgressHolder
import androidx.media3.transformer.Transformer
import androidx.media3.transformer.VideoEncoderSettings
import com.arthenica.ffmpegkit.FFmpegKit
import com.arthenica.ffmpegkit.ReturnCode
import kotlinx.coroutines.CancellationException
import kotlinx.coroutines.CoroutineScope
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.Job
import kotlinx.coroutines.SupervisorJob
import kotlinx.coroutines.cancel
import kotlinx.coroutines.delay
import kotlinx.coroutines.ensureActive
import kotlinx.coroutines.isActive
import kotlinx.coroutines.launch
import kotlinx.coroutines.suspendCancellableCoroutine
import kotlinx.coroutines.withContext
import java.io.File
import kotlin.coroutines.resume

class VideoImportService : Service() {
    private val scope = CoroutineScope(Dispatchers.Main + SupervisorJob())
    private var importJob: Job? = null
    private var activeFfmpegSessionId: Long? = null
    private var mediaTransformer: Transformer? = null
    private var currentTempFile: File? = null

    override fun onCreate() {
        super.onCreate()
        createNotificationChannel()
    }

    override fun onBind(intent: Intent?): IBinder? = null

    override fun onStartCommand(intent: Intent?, flags: Int, startId: Int): Int {
        if (intent?.action == ACTION_CANCEL) {
            cancelActiveImport()
            return START_NOT_STICKY
        }

        if (importJob?.isActive == true) return START_NOT_STICKY
        val request = VideoImportQueue.dequeue()
        if (request == null) {
            stopSelf()
            return START_NOT_STICKY
        }

        startForeground(NOTIFICATION_ID, buildNotification("가져오기 준비 중", 0, true, ongoing = true))
        startImport(request)
        return START_NOT_STICKY
    }

    override fun onDestroy() {
        cancelActiveImport()
        scope.cancel()
        super.onDestroy()
    }

    private fun startImport(request: VideoImportRequest) {
        importJob = scope.launch {
            val importedFiles = mutableListOf<File>()
            val sourceUris = mutableListOf<Uri>()
            try {
                request.items.forEachIndexed { index, item ->
                    ensureActive()
                    val policy = VideoImportPolicy.evaluate(
                        width = item.width,
                        height = item.height,
                        bitrate = item.bitrate,
                        option = request.option
                    )
                    val action = if (policy.shouldCompress) "압축 중" else "원본 복사 중"
                    updateProgress(action, item.title, index, request.items.size, 0)
                    val sourceUri = Uri.parse(item.uri)
                    val outputFile = if (policy.shouldCompress) {
                        compressSelectedVideo(sourceUri, item, policy) { progress ->
                            updateProgress(action, item.title, index, request.items.size, progress)
                        }
                    } else {
                        copySelectedVideo(sourceUri, item) { progress ->
                            updateProgress(action, item.title, index, request.items.size, progress)
                        }
                    }
                    importedFiles += outputFile
                    sourceUris += sourceUri
                    updateProgress("완료", item.title, index, request.items.size, 100)
                }

                val deletionSummary = if (request.deleteSourceAfterImport) {
                    withContext(Dispatchers.IO) {
                        VideoSourceDeletionPolicy.deleteImportedSources(sourceUris.size) { index ->
                            deleteOriginalSource(sourceUris[index])
                        }
                    }
                } else {
                    VideoSourceDeletionSummary(deletedCount = 0, failedCount = 0)
                }
                val message = if (deletionSummary.failedCount > 0) {
                    "가져오기 완료: ${importedFiles.size}개, 원본 삭제 실패: ${deletionSummary.failedCount}개"
                } else {
                    "가져오기 완료: ${importedFiles.size}개"
                }
                finish(message, success = true)
            } catch (_: CancellationException) {
                finish("가져오기를 취소했습니다.", success = false)
            } catch (e: Exception) {
                Log.e(DEBUG_TAG, "video import failed: ${e.message}", e)
                finish("가져오기에 실패했습니다: ${e.message ?: e.javaClass.simpleName}", success = false)
            } catch (t: Throwable) {
                Log.e(DEBUG_TAG, "fatal video import failure: ${t.message}", t)
                finish("가져오기에 실패했습니다: ${t.javaClass.simpleName}", success = false)
            } finally {
                importedFiles.clear()
                currentTempFile?.delete()
                currentTempFile = null
                importJob = null
                stopSelf()
            }
        }
    }

    private suspend fun copySelectedVideo(
        uri: Uri,
        item: VideoImportItem,
        onProgress: (Int) -> Unit
    ): File {
        val outputFile = uniqueVideoFile(item.title)
        return try {
            copyUriToFile(uri, item, outputFile, onProgress)
            outputFile
        } catch (error: CancellationException) {
            outputFile.delete()
            throw error
        }
    }

    private suspend fun compressSelectedVideo(
        uri: Uri,
        item: VideoImportItem,
        policy: VideoImportPolicy,
        onProgress: (Int) -> Unit
    ): File {
        val outputFile = uniqueVideoFile(VideoImportFileName.compressedOutputName(item.title))
        val extension = item.title.substringAfterLast('.', "mp4").ifBlank { "mp4" }
        val inputTempFile = File(cacheDir, "import_input_${System.currentTimeMillis()}.$extension")
        currentTempFile = inputTempFile

        return try {
            copyUriToFile(uri, item, inputTempFile) { progress ->
                onProgress((progress * 5 / 100).coerceIn(0, 5))
            }
            executeFfmpegImportOrFallback(inputTempFile, outputFile, policy, item.durationMs) { progress ->
                onProgress((5 + (progress * 94 / 100)).coerceIn(5, 99))
            }
            onProgress(100)
            outputFile
        } catch (error: CancellationException) {
            outputFile.delete()
            throw error
        } finally {
            currentTempFile = null
            inputTempFile.delete()
        }
    }

    private suspend fun copyUriToFile(
        uri: Uri,
        item: VideoImportItem,
        outputFile: File,
        onProgress: (Int) -> Unit
    ) {
        withContext(Dispatchers.IO) {
            contentResolver.openInputStream(uri)?.use { input ->
                outputFile.outputStream().use { output ->
                    val totalBytes = item.sizeBytes?.takeIf { it > 0L }
                    val buffer = ByteArray(DEFAULT_BUFFER_SIZE)
                    var copiedBytes = 0L
                    var lastProgress = -1
                    while (true) {
                        ensureActive()
                        val read = input.read(buffer)
                        if (read < 0) break
                        output.write(buffer, 0, read)
                        copiedBytes += read
                        val progress = totalBytes
                            ?.let { ((copiedBytes * 100L) / it).toInt().coerceIn(0, 99) }
                            ?: 50
                        if (progress != lastProgress) {
                            lastProgress = progress
                            onProgress(progress)
                        }
                    }
                    onProgress(100)
                }
            } ?: error("선택한 파일을 열 수 없습니다.")
        }
    }

    private suspend fun executeFfmpegImportOrFallback(
        inputFile: File,
        outputFile: File,
        policy: VideoImportPolicy,
        durationMs: Long?,
        onProgress: (Int) -> Unit
    ) {
        try {
            runFfmpegCommand(
                args = FfmpegImportCommand.hardware(inputFile.absolutePath, outputFile.absolutePath, policy),
                durationMs = durationMs,
                onProgress = onProgress
            ).recoverCatching { firstError ->
                outputFile.delete()
                runFfmpegCommand(
                    args = FfmpegImportCommand.softwareFallback(inputFile.absolutePath, outputFile.absolutePath, policy),
                    durationMs = durationMs,
                    onProgress = onProgress
                ).getOrElse { throw firstError }
            }.getOrThrow()
        } catch (error: Throwable) {
            if (error is CancellationException) throw error
            if (!FfmpegRuntimeAvailability.isUnavailable(error)) throw error
            outputFile.delete()
            exportVideoWithMedia3(
                inputUri = Uri.fromFile(inputFile),
                outputFile = outputFile,
                policy = policy,
                onProgress = onProgress
            )
        }
    }

    private suspend fun runFfmpegCommand(
        args: Array<String>,
        durationMs: Long?,
        onProgress: (Int) -> Unit
    ): Result<Unit> =
        suspendCancellableCoroutine { continuation ->
            val session = FFmpegKit.executeWithArgumentsAsync(
                args,
                { session ->
                    activeFfmpegSessionId = null
                    val returnCode = session.returnCode
                    when {
                        ReturnCode.isSuccess(returnCode) -> {
                            if (continuation.isActive) continuation.resume(Result.success(Unit))
                        }
                        ReturnCode.isCancel(returnCode) -> {
                            if (continuation.isActive) continuation.cancel()
                        }
                        else -> {
                            val message = session.failStackTrace ?: session.allLogsAsString ?: "FFmpeg 압축 실패"
                            if (continuation.isActive) continuation.resume(Result.failure(IllegalStateException(message)))
                        }
                    }
                },
                null,
                { statistics ->
                    val duration = durationMs?.takeIf { it > 0L } ?: return@executeWithArgumentsAsync
                    val progress = ((statistics.time * 100.0) / duration).toInt().coerceIn(0, 99)
                    onProgress(progress)
                }
            )
            activeFfmpegSessionId = session.sessionId
            continuation.invokeOnCancellation {
                activeFfmpegSessionId?.let(FFmpegKit::cancel)
                activeFfmpegSessionId = null
            }
        }

    private suspend fun exportVideoWithMedia3(
        inputUri: Uri,
        outputFile: File,
        policy: VideoImportPolicy,
        onProgress: (Int) -> Unit
    ) =
        suspendCancellableCoroutine<Unit> { continuation ->
            val editedMediaItem = EditedMediaItem.Builder(MediaItem.fromUri(inputUri))
                .setFrameRate(policy.targetFrameRate)
                .setEffects(
                    Effects(
                        emptyList<AudioProcessor>(),
                        listOf<Effect>(Presentation.createForHeight(policy.targetHeight))
                    )
                )
                .build()

            val encoderFactory = DefaultEncoderFactory.Builder(this)
                .setRequestedVideoEncoderSettings(
                    VideoEncoderSettings.Builder()
                        .setBitrate(policy.targetBitrate)
                        .build()
                )
                .setEnableFallback(true)
                .build()

            var progressJob: Job? = null
            mediaTransformer = Transformer.Builder(this)
                .setEncoderFactory(encoderFactory)
                .setVideoMimeType(MimeTypes.VIDEO_H265)
                .setAudioMimeType(MimeTypes.AUDIO_AAC)
                .addListener(
                    object : Transformer.Listener {
                        override fun onCompleted(composition: Composition, result: ExportResult) {
                            progressJob?.cancel()
                            onProgress(100)
                            mediaTransformer = null
                            if (continuation.isActive) continuation.resume(Unit)
                        }

                        override fun onError(
                            composition: Composition,
                            result: ExportResult,
                            exception: ExportException
                        ) {
                            progressJob?.cancel()
                            mediaTransformer = null
                            if (continuation.isActive) continuation.cancel(exception)
                        }
                    }
                )
                .build()

            continuation.invokeOnCancellation {
                progressJob?.cancel()
                mediaTransformer?.cancel()
                mediaTransformer = null
            }

            val activeTransformer = mediaTransformer
            progressJob = scope.launch {
                val holder = ProgressHolder()
                while (isActive && activeTransformer != null) {
                    val state = activeTransformer.getProgress(holder)
                    if (state == Transformer.PROGRESS_STATE_AVAILABLE) {
                        onProgress(holder.progress.coerceIn(0, 99))
                    }
                    delay(250)
                }
            }
            activeTransformer?.start(editedMediaItem, outputFile.absolutePath)
        }

    private fun deleteOriginalSource(uri: Uri): Boolean =
        when (uri.scheme) {
            "content" -> tryDeleteDocument(uri) || runCatching {
                contentResolver.delete(uri, null, null) > 0
            }.getOrDefault(false)
            "file" -> uri.path?.let { path -> runCatching { File(path).delete() }.getOrDefault(false) } == true
            else -> false
        }

    private fun tryDeleteDocument(uri: Uri): Boolean =
        runCatching {
            DocumentsContract.deleteDocument(contentResolver, uri)
        }.getOrDefault(false)

    private fun updateProgress(action: String, title: String, fileIndex: Int, totalFiles: Int, fileProgress: Int) {
        val boundedFileProgress = fileProgress.coerceIn(0, 100)
        val totalProgress = (((fileIndex * 100) + boundedFileProgress) / totalFiles).coerceIn(0, 100)
        val message = "$action (${fileIndex + 1}/$totalFiles): $title"
        val manager = getSystemService(Context.NOTIFICATION_SERVICE) as NotificationManager
        manager.notify(NOTIFICATION_ID, buildNotification(message, totalProgress, false, ongoing = true))
    }

    private fun finish(message: String, success: Boolean) {
        val manager = getSystemService(Context.NOTIFICATION_SERVICE) as NotificationManager
        manager.notify(NOTIFICATION_ID, buildNotification(message, 100, false, ongoing = false, success = success))
        sendBroadcast(Intent(ACTION_IMPORT_CHANGED).setPackage(packageName))
    }

    private fun buildNotification(
        message: String,
        progress: Int,
        indeterminate: Boolean,
        ongoing: Boolean,
        success: Boolean = true
    ) =
        NotificationCompat.Builder(this, CHANNEL_ID)
            .setSmallIcon(if (success) android.R.drawable.stat_sys_upload_done else android.R.drawable.stat_notify_error)
            .setContentTitle("영상 가져오기")
            .setContentText(message)
            .setContentIntent(
                PendingIntent.getActivity(
                    this,
                    0,
                    Intent(this, MainActivity::class.java),
                    PendingIntent.FLAG_UPDATE_CURRENT or PendingIntent.FLAG_IMMUTABLE
                )
            )
            .addAction(
                android.R.drawable.ic_menu_close_clear_cancel,
                "취소",
                PendingIntent.getService(
                    this,
                    1,
                    Intent(this, VideoImportService::class.java).apply { action = ACTION_CANCEL },
                    PendingIntent.FLAG_UPDATE_CURRENT or PendingIntent.FLAG_IMMUTABLE
                )
            )
            .setOngoing(ongoing)
            .setAutoCancel(!ongoing)
            .setOnlyAlertOnce(true)
            .setPriority(if (success) NotificationCompat.PRIORITY_LOW else NotificationCompat.PRIORITY_HIGH)
            .setProgress(100, progress.coerceIn(0, 100), indeterminate)
            .build()

    private fun cancelActiveImport() {
        activeFfmpegSessionId?.let(FFmpegKit::cancel)
        activeFfmpegSessionId = null
        mediaTransformer?.cancel()
        mediaTransformer = null
        currentTempFile?.delete()
        currentTempFile = null
        importJob?.cancel()
    }

    private fun uniqueVideoFile(fileName: String): File {
        val cleanName = fileName.ifBlank { "Meet_${System.currentTimeMillis()}.mp4" }
        val baseName = cleanName.substringBeforeLast('.', cleanName)
        val extension = cleanName.substringAfterLast('.', "mp4").ifBlank { "mp4" }
        var candidate = File(videosDir(), "$baseName.$extension")
        var index = 1
        while (candidate.exists()) {
            candidate = File(videosDir(), "${baseName}_$index.$extension")
            index++
        }
        return candidate
    }

    private fun videosDir(): File =
        File(getExternalFilesDir(null), HlsDownloadOutputPolicy.libraryDirectoryName).apply { if (!exists()) mkdirs() }

    private fun createNotificationChannel() {
        if (Build.VERSION.SDK_INT < Build.VERSION_CODES.O) return
        val manager = getSystemService(Context.NOTIFICATION_SERVICE) as NotificationManager
        manager.createNotificationChannel(
            NotificationChannel(
                CHANNEL_ID,
                "영상 가져오기",
                NotificationManager.IMPORTANCE_LOW
            )
        )
    }

    companion object {
        const val ACTION_IMPORT_CHANGED = "com.kys.videomanager.import.CHANGED"
        private const val ACTION_CANCEL = "com.kys.videomanager.import.CANCEL"
        private const val CHANNEL_ID = "video_import"
        private const val NOTIFICATION_ID = 3001
        private const val DEBUG_TAG = "DDDDD"

        fun start(context: Context, request: VideoImportRequest) {
            VideoImportQueue.enqueue(request)
            val intent = Intent(context, VideoImportService::class.java)
            androidx.core.content.ContextCompat.startForegroundService(context, intent)
        }
    }
}
