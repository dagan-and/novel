package com.kys.videomanager.videotrim
import com.kys.videomanager.R
import com.kys.videomanager.ffmpeg.FfmpegTrimCommand
import com.kys.videomanager.hls.HlsDownloadOutputPolicy
import com.kys.videomanager.main.MainActivity
import com.kys.videomanager.video.VideoFileNameSanitizer

import android.app.NotificationChannel
import android.app.NotificationManager
import android.app.PendingIntent
import android.app.Service
import android.content.Context
import android.content.Intent
import android.os.Build
import android.os.IBinder
import android.util.Log
import androidx.core.app.NotificationCompat
import com.arthenica.ffmpegkit.FFmpegKit
import com.arthenica.ffmpegkit.ReturnCode
import kotlinx.coroutines.CancellationException
import kotlinx.coroutines.CoroutineScope
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.SupervisorJob
import kotlinx.coroutines.cancel
import kotlinx.coroutines.launch
import kotlinx.coroutines.suspendCancellableCoroutine
import java.io.File
import kotlin.coroutines.resume

class VideoTrimService : Service() {
    private val scope = CoroutineScope(Dispatchers.Main + SupervisorJob())
    private var activeFfmpegSessionId: Long? = null
    private var activeOutputFile: File? = null

    override fun onCreate() {
        super.onCreate()
        createNotificationChannel()
    }

    override fun onBind(intent: Intent?): IBinder? = null

    override fun onStartCommand(intent: Intent?, flags: Int, startId: Int): Int {
        if (intent?.action == ACTION_CANCEL) {
            cancelActiveTrim()
            return START_NOT_STICKY
        }

        val request = VideoTrimQueue.dequeue()
        if (request == null) {
            stopSelf()
            return START_NOT_STICKY
        }

        startForeground(NOTIFICATION_ID, buildNotification("자르기 준비 중", 0, true, ongoing = true))
        startTrim(request)
        return START_NOT_STICKY
    }

    override fun onDestroy() {
        cancelActiveTrim()
        scope.cancel()
        super.onDestroy()
    }

    private fun startTrim(request: VideoTrimRequest) {
        scope.launch {
            val inputFile = File(request.inputPath)
            val outputFile = uniqueVideoFile(request.outputName)
            activeOutputFile = outputFile
            try {
                if (!inputFile.isFile) error("원본 파일을 찾을 수 없습니다.")
                runFfmpegCommand(
                    args = FfmpegTrimCommand.fastCopy(
                        inputPath = inputFile.absolutePath,
                        outputPath = outputFile.absolutePath,
                        startSeconds = request.startSeconds,
                        endSeconds = request.endSeconds
                    ),
                    durationMs = (request.endSeconds - request.startSeconds) * 1000L
                ) { progress ->
                    updateProgress(inputFile.name, progress)
                }.getOrThrow()
                if (!VideoTrimOutputValidator.isUsable(outputFile)) {
                    outputFile.delete()
                    error("결과 파일이 비어 있습니다.")
                }
                finish("자르기 완료: ${outputFile.name}", success = true)
            } catch (_: CancellationException) {
                outputFile.delete()
                finish("자르기를 취소했습니다.", success = false)
            } catch (e: Exception) {
                outputFile.delete()
                Log.e(DEBUG_TAG, "video trim failed: ${e.message}", e)
                finish("자르기에 실패했습니다: ${e.message ?: e.javaClass.simpleName}", success = false)
            } finally {
                activeOutputFile = null
                stopSelf()
            }
        }
    }

    private suspend fun runFfmpegCommand(
        args: Array<String>,
        durationMs: Long,
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
                            val message = session.failStackTrace ?: session.allLogsAsString ?: "FFmpeg 자르기 실패"
                            if (continuation.isActive) continuation.resume(Result.failure(IllegalStateException(message)))
                        }
                    }
                },
                null,
                { statistics ->
                    val progress = ((statistics.time * 100.0) / durationMs).toInt().coerceIn(0, 99)
                    onProgress(progress)
                }
            )
            activeFfmpegSessionId = session.sessionId
            continuation.invokeOnCancellation {
                activeFfmpegSessionId?.let(FFmpegKit::cancel)
                activeFfmpegSessionId = null
            }
        }

    private fun updateProgress(fileName: String, progress: Int) {
        val manager = getSystemService(Context.NOTIFICATION_SERVICE) as NotificationManager
        manager.notify(
            NOTIFICATION_ID,
            buildNotification("자르기 중: $fileName", progress.coerceIn(0, 99), false, ongoing = true)
        )
    }

    private fun finish(message: String, success: Boolean) {
        val manager = getSystemService(Context.NOTIFICATION_SERVICE) as NotificationManager
        manager.notify(NOTIFICATION_ID, buildNotification(message, 100, false, ongoing = false, success = success))
        sendBroadcast(Intent(ACTION_TRIM_CHANGED).setPackage(packageName))
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
            .setContentTitle("영상 자르기")
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
                    Intent(this, VideoTrimService::class.java).apply { action = ACTION_CANCEL },
                    PendingIntent.FLAG_UPDATE_CURRENT or PendingIntent.FLAG_IMMUTABLE
                )
            )
            .setOngoing(ongoing)
            .setAutoCancel(!ongoing)
            .setOnlyAlertOnce(true)
            .setPriority(if (success) NotificationCompat.PRIORITY_LOW else NotificationCompat.PRIORITY_HIGH)
            .setProgress(100, progress.coerceIn(0, 100), indeterminate)
            .build()

    private fun cancelActiveTrim() {
        activeFfmpegSessionId?.let(FFmpegKit::cancel)
        activeFfmpegSessionId = null
        activeOutputFile?.delete()
        activeOutputFile = null
    }

    private fun uniqueVideoFile(fileName: String): File {
        val cleanName = fileName.ifBlank { "Meet_${System.currentTimeMillis()}.mp4" }
        val baseName = VideoFileNameSanitizer.sanitizeBaseName(cleanName.substringBeforeLast('.', cleanName))
        val extension = VideoFileNameSanitizer.sanitizeExtension(cleanName.substringAfterLast('.', "mp4"))
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
                "영상 자르기",
                NotificationManager.IMPORTANCE_LOW
            )
        )
    }

    companion object {
        const val ACTION_TRIM_CHANGED = "com.kys.videomanager.trim.CHANGED"
        private const val ACTION_CANCEL = "com.kys.videomanager.trim.CANCEL"
        private const val CHANNEL_ID = "video_trim"
        private const val NOTIFICATION_ID = 3002
        private const val DEBUG_TAG = "DDDDD"

        fun start(context: Context, request: VideoTrimRequest) {
            VideoTrimQueue.enqueue(request)
            val intent = Intent(context, VideoTrimService::class.java)
            androidx.core.content.ContextCompat.startForegroundService(context, intent)
        }
    }
}
