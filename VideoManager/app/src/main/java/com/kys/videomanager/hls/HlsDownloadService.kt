package com.kys.videomanager.hls

import com.kys.videomanager.downloadstatus.DownloadStatusActivity
import com.kys.videomanager.hlsplaylist.HlsPlaylistParseResult
import com.kys.videomanager.hlsplaylist.HlsPlaylistParser
import com.kys.videomanager.hlsplaylist.HlsPlaylistResumeGuard
import com.kys.videomanager.hlsplaylist.HlsProbeRequest
import com.kys.videomanager.hlsplaylist.HlsRequestProbe
import com.kys.videomanager.R

import android.app.NotificationChannel
import android.app.NotificationManager
import android.app.PendingIntent
import android.app.Service
import android.content.Context
import android.content.Intent
import android.os.Build
import android.os.IBinder
import android.text.format.Formatter
import android.util.Log
import androidx.core.app.NotificationCompat
import kotlinx.coroutines.CoroutineScope
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.Job
import kotlinx.coroutines.SupervisorJob
import kotlinx.coroutines.cancel
import kotlinx.coroutines.delay
import kotlinx.coroutines.ensureActive
import kotlinx.coroutines.launch
import java.io.File
import java.io.FileOutputStream
import java.net.HttpURLConnection
import java.net.URL
import java.util.Locale
import java.util.concurrent.ConcurrentHashMap
import kotlin.coroutines.coroutineContext

class HlsDownloadService : Service() {
    private val scope = CoroutineScope(Dispatchers.IO + SupervisorJob())
    private val downloadJobs = ConcurrentHashMap<String, Job>()
    private val tokenRefresher by lazy { HlsTokenRefresher(applicationContext) }

    override fun onCreate() {
        super.onCreate()
        createNotificationChannel()
    }

    override fun onBind(intent: Intent?): IBinder? = null

    override fun onStartCommand(intent: Intent?, flags: Int, startId: Int): Int {
        HlsDownloadStore.initialize(applicationContext)
        when (intent?.action) {
            ACTION_CANCEL -> {
                cancelAllDownloads()
                stopSelf()
            }
            ACTION_CANCEL_ONE -> {
                cancelDownload(intent.getStringExtra(EXTRA_DOWNLOAD_ID))
            }
            ACTION_RETRY -> {
                retryDownload(intent.getStringExtra(EXTRA_DOWNLOAD_ID))
            }
            else -> {
                val request = HlsDownloadStore.dequeue()
                if (request == null) {
                    stopSelf()
                    return START_NOT_STICKY
                }
                startForeground(NOTIFICATION_ID, buildNotification(HlsDownloadProgress(message = "다운로드 준비 중")))
                startDownload(request)
            }
        }
        return START_NOT_STICKY
    }

    override fun onDestroy() {
        downloadJobs.values.forEach { it.cancel() }
        downloadJobs.clear()
        scope.cancel()
        super.onDestroy()
    }

    private fun startDownload(request: HlsDownloadRequest) {
        if (downloadJobs.containsKey(request.id)) return
        val job = scope.launch {
            var completedAttempts = 0
            var currentRequest = request
            try {
                while (true) {
                    try {
                        runDownloadAttempt(currentRequest)
                        return@launch
                    } catch (error: kotlinx.coroutines.CancellationException) {
                        throw error
                    } catch (error: Exception) {
                        val decision = HlsDownloadRetryPolicy.retryDecision(error, completedAttempts)
                        if (!decision.shouldRetry) {
                            fail(currentRequest, finalFailureMessage(error, completedAttempts))
                            return@launch
                        }
                        completedAttempts++
                        currentRequest = HlsDownloadStore.retryProgress(currentRequest.id)?.request ?: currentRequest
                        scheduleRetry(currentRequest, completedAttempts, decision.delayMillis, error)
                        delay(decision.delayMillis)
                    }
                }
            } catch (_: kotlinx.coroutines.CancellationException) {
                val previous = HlsDownloadStore.retryProgress(currentRequest.id)
                update(
                    HlsDownloadProgress(
                        id = currentRequest.id,
                        status = HlsDownloadStatus.CANCELED,
                        title = currentRequest.title,
                        playlistUrl = currentRequest.playlistUrl,
                        downloadedSegments = previous?.downloadedSegments ?: 0,
                        totalSegments = previous?.totalSegments ?: 0,
                        downloadedBytes = previous?.downloadedBytes ?: 0L,
                        outputPath = previous?.outputPath,
                        message = "다운로드를 일시 중단했습니다. 다시 시도하면 이어받습니다.",
                        request = currentRequest
                    )
                )
            } catch (t: Throwable) {
                Log.e(DEBUG_TAG, "fatal download failure converted to failed state: ${t.message}", t)
                fail(currentRequest, "다운로드 실패: ${t.javaClass.simpleName}: ${t.message ?: "알 수 없는 오류"}")
            } finally {
                // Conditional remove: a manual retry may have already replaced this id's
                // entry with a new job (see retryDownload()) — don't evict that one.
                downloadJobs.remove(currentRequest.id, coroutineContext[Job])
                if (downloadJobs.isEmpty()) stopSelf()
            }
        }
        downloadJobs[request.id] = job
    }

    private suspend fun runDownloadAttempt(request: HlsDownloadRequest) {
        update(
            HlsDownloadProgress(
                id = request.id,
                status = HlsDownloadStatus.FETCHING_PLAYLIST,
                title = request.title,
                playlistUrl = request.playlistUrl,
                message = "playlist 확인 중",
                request = request
            )
        )

        val resolved = resolveMediaPlaylist(request)
        val currentRequest = resolved.request
        val playlist = resolved.parseResult
        if (playlist.isEncrypted) {
            throw HlsDownloadException("암호화된 HLS는 지원하지 않습니다.", HlsDownloadFailureKind.UNSUPPORTED)
        }
        if (playlist.segmentUrls.isEmpty()) {
            throw HlsDownloadException("다운로드할 세그먼트를 찾지 못했습니다.", HlsDownloadFailureKind.NOT_RETRYABLE)
        }

        val tempTsFile = createTempTsFile(currentRequest)
        val previousProgress = HlsDownloadStore.retryProgress(currentRequest.id)
        if (HlsPlaylistResumeGuard.shouldRestartFromScratch(previousProgress?.totalSegments ?: 0, playlist.segmentUrls.size)) {
            tempTsFile.delete()
        }
        val resumeSegmentCount = resumeSegmentCount(previousProgress, tempTsFile, playlist.segmentUrls.size)
        val outputFile = previousProgress
            ?.outputPath
            ?.takeIf { it.isNotBlank() }
            ?.let { File(it) }
            ?: createDownloadsOutputFile(currentRequest.title, HlsDownloadOutputPolicy.downloadExtension)
        var downloadedBytes = if (resumeSegmentCount > 0) tempTsFile.length() else 0L
        if (resumeSegmentCount > 0) {
            update(
                HlsDownloadProgress(
                    id = currentRequest.id,
                    status = HlsDownloadStatus.DOWNLOADING,
                    title = currentRequest.title,
                    playlistUrl = currentRequest.playlistUrl,
                    downloadedSegments = resumeSegmentCount,
                    totalSegments = playlist.segmentUrls.size,
                    downloadedBytes = downloadedBytes,
                    outputPath = outputFile.absolutePath,
                    message = "${resumeSegmentCount}/${playlist.segmentUrls.size} 세그먼트부터 이어받는 중",
                    request = currentRequest
                )
            )
        }
        FileOutputStream(tempTsFile, resumeSegmentCount > 0).use { output ->
            playlist.segmentUrls.drop(resumeSegmentCount).forEachIndexed { offset, segmentUrl ->
                coroutineContext.ensureActive()
                downloadedBytes += appendUrlTo(segmentUrl, currentRequest, output)
                val downloadedSegments = resumeSegmentCount + offset + 1
                update(
                    HlsDownloadProgress(
                        id = currentRequest.id,
                        status = HlsDownloadStatus.DOWNLOADING,
                        title = currentRequest.title,
                        playlistUrl = currentRequest.playlistUrl,
                        downloadedSegments = downloadedSegments,
                        totalSegments = playlist.segmentUrls.size,
                        downloadedBytes = downloadedBytes,
                        outputPath = outputFile.absolutePath,
                        message = "${downloadedSegments}/${playlist.segmentUrls.size} 세그먼트 저장 중",
                        request = currentRequest
                    )
                )
            }
        }

        tempTsFile.copyTo(outputFile, overwrite = true)
        tempTsFile.delete()

        update(
            HlsDownloadProgress(
                id = currentRequest.id,
                status = HlsDownloadStatus.COMPLETED,
                title = currentRequest.title,
                playlistUrl = currentRequest.playlistUrl,
                downloadedSegments = playlist.segmentUrls.size,
                totalSegments = playlist.segmentUrls.size,
                downloadedBytes = outputFile.length(),
                outputPath = outputFile.absolutePath,
                message = "TS 다운로드 완료: ${Formatter.formatFileSize(this@HlsDownloadService, outputFile.length())}"
            )
        )
    }

    private data class HlsResolvedPlaylist(
        val parseResult: HlsPlaylistParseResult,
        val request: HlsDownloadRequest
    )

    private suspend fun resolveMediaPlaylist(initialRequest: HlsDownloadRequest): HlsResolvedPlaylist {
        var currentRequest = initialRequest
        var currentUrl = currentRequest.playlistUrl
        var refreshAttempts = 0
        var depth = 0
        while (true) {
            val text = try {
                fetchText(currentUrl, currentRequest)
            } catch (error: HlsDownloadException) {
                if (HlsTokenRefreshPolicy.shouldAttemptRefresh(error, refreshAttempts)) {
                    refreshAttempts++
                    val refreshed = currentRequest.pageUrl?.let { tokenRefresher.refresh(it) }
                        ?: throw error
                    currentRequest = currentRequest.copy(
                        playlistUrl = refreshed.playlistUrl,
                        requestHeaders = refreshed.requestHeaders,
                        cookie = refreshed.cookie
                    )
                    currentUrl = currentRequest.playlistUrl
                    persistRefreshedRequest(currentRequest)
                    continue
                }
                if (HlsTokenRefreshPolicy.isTokenBlockedFailure(error)) {
                    throw HlsDownloadException(
                        "사이트에서 새 접근 권한을 받지 못해 다운로드를 중단했습니다. 페이지를 열어 다시 시도해 주세요.",
                        HlsDownloadFailureKind.NOT_RETRYABLE,
                        stage = error.stage,
                        httpCode = error.httpCode
                    )
                }
                throw error
            }
            val parsed = HlsPlaylistParser.parse(currentUrl, text)
            if (!parsed.isMaster) return HlsResolvedPlaylist(parsed, currentRequest)
            val variantUrl = parsed.variantUrl ?: return HlsResolvedPlaylist(parsed, currentRequest)
            depth++
            if (depth >= MAX_PLAYLIST_DEPTH) {
                return HlsResolvedPlaylist(
                    HlsPlaylistParseResult(isMaster = true, variantUrl = variantUrl, segmentUrls = emptyList(), isEncrypted = false),
                    currentRequest
                )
            }
            currentUrl = variantUrl
        }
    }

    private fun persistRefreshedRequest(request: HlsDownloadRequest) {
        val previous = HlsDownloadStore.retryProgress(request.id)
        update(
            HlsDownloadProgress(
                id = request.id,
                status = HlsDownloadStatus.FETCHING_PLAYLIST,
                title = request.title,
                playlistUrl = request.playlistUrl,
                downloadedSegments = previous?.downloadedSegments ?: 0,
                totalSegments = previous?.totalSegments ?: 0,
                downloadedBytes = previous?.downloadedBytes ?: 0L,
                outputPath = previous?.outputPath,
                message = "새로운 접근 권한을 확인했습니다. 이어서 진행합니다",
                request = request
            )
        )
    }

    private fun fetchText(url: String, request: HlsDownloadRequest): String {
        val connection = openConnection(url, request)
        return try {
            val code = connection.responseCode
            if (code !in 200..399) {
                throw httpFailure("HTTP $code", code, connection.getHeaderField("Retry-After"), HlsDownloadStage.PLAYLIST)
            }
            connection.inputStream.bufferedReader().use { it.readText() }
        } finally {
            connection.disconnect()
        }
    }

    private suspend fun appendUrlTo(url: String, request: HlsDownloadRequest, output: FileOutputStream): Long {
        var attempt = 1
        while (true) {
            val connection = openConnection(url, request)
            try {
                val code = connection.responseCode
                if (code !in 200..399) {
                    val decision = HlsSegmentRetryPolicy.retryDecision(
                        responseCode = code,
                        retryAfterHeader = connection.getHeaderField("Retry-After"),
                        attempt = attempt
                    )
                    if (decision.shouldRetry) {
                        Log.w(DEBUG_TAG, "segment HTTP $code, retrying in ${decision.delayMillis}ms attempt=$attempt url=$url")
                        delay(decision.delayMillis)
                        attempt++
                        continue
                    }
                    throw httpFailure("segment HTTP $code", code, connection.getHeaderField("Retry-After"), HlsDownloadStage.SEGMENT)
                }
                var total = 0L
                val buffer = ByteArray(DEFAULT_BUFFER_SIZE)
                connection.inputStream.use { input ->
                    while (true) {
                        val read = input.read(buffer)
                        if (read == -1) break
                        output.write(buffer, 0, read)
                        total += read
                    }
                }
                return total
            } finally {
                connection.disconnect()
            }
        }
    }

    private fun httpFailure(
        message: String,
        responseCode: Int,
        retryAfterHeader: String?,
        stage: HlsDownloadStage
    ): HlsDownloadException =
        HlsDownloadException(
            message = message,
            kind = when (responseCode) {
                in TRANSIENT_HTTP_CODES -> HlsDownloadFailureKind.TRANSIENT
                401, 403, 404, 410 -> HlsDownloadFailureKind.NOT_RETRYABLE
                else -> HlsDownloadFailureKind.NOT_RETRYABLE
            },
            retryAfterMillis = retryAfterHeader?.trim()?.toLongOrNull()?.coerceAtLeast(0L)?.times(1_000L),
            stage = stage,
            httpCode = responseCode
        )

    private fun scheduleRetry(
        request: HlsDownloadRequest,
        retryNumber: Int,
        delayMillis: Long,
        error: Throwable
    ) {
        val previous = HlsDownloadStore.retryProgress(request.id)
        val minutes = (delayMillis / 60_000L).coerceAtLeast(1L)
        update(
            HlsDownloadProgress(
                id = request.id,
                status = HlsDownloadStatus.IDLE,
                title = request.title,
                playlistUrl = request.playlistUrl,
                downloadedSegments = previous?.downloadedSegments ?: 0,
                totalSegments = previous?.totalSegments ?: 0,
                downloadedBytes = previous?.downloadedBytes ?: 0L,
                outputPath = previous?.outputPath,
                message = "일시적인 오류로 ${minutes}분 후 자동 재시도합니다. ($retryNumber/${HlsDownloadRetryPolicy.maxRetries}) ${error.shortReason()}",
                request = request
            )
        )
    }

    private fun finalFailureMessage(error: Throwable, completedAttempts: Int): String {
        val reason = error.shortReason()
        val retrySuffix = if (completedAttempts > 0) " 자동 재시도 ${completedAttempts}회 후 중단했습니다." else ""
        return "다운로드 실패: $reason$retrySuffix"
    }

    private fun Throwable.shortReason(): String =
        when (this) {
            is HlsDownloadException -> message ?: javaClass.simpleName
            else -> message ?: javaClass.simpleName
        }

    private fun resumeSegmentCount(
        previousProgress: HlsDownloadProgress?,
        tempTsFile: File,
        totalSegments: Int
    ): Int {
        val downloadedSegments = previousProgress?.downloadedSegments ?: return 0
        if (!tempTsFile.exists() || tempTsFile.length() <= 0L) return 0
        if (downloadedSegments <= 0 || downloadedSegments >= totalSegments) return 0
        return downloadedSegments
    }

    private fun openConnection(url: String, request: HlsDownloadRequest): HttpURLConnection {
        return (URL(url).openConnection() as HttpURLConnection).apply {
            connectTimeout = CONNECT_TIMEOUT_MS
            readTimeout = READ_TIMEOUT_MS
            instanceFollowRedirects = true
            HlsRequestProbe.buildHeaders(
                HlsProbeRequest(
                    url = url,
                    pageUrl = request.pageUrl,
                    requestHeaders = request.requestHeaders,
                    cookie = request.cookie
                )
            ).forEach { (name, value) -> setRequestProperty(name, value) }
        }
    }

    private fun createTempTsFile(request: HlsDownloadRequest): File {
        val directory = File(cacheDir, "hls").apply { mkdirs() }
        return File(directory, "${request.id}.ts")
    }

    private fun createDownloadsOutputFile(title: String, extension: String): File {
        val directory = File(filesDir, HlsDownloadOutputPolicy.downloadDirectoryName).apply { mkdirs() }
        val baseName = title
            .ifBlank { "hls_${System.currentTimeMillis()}" }
            .replace(Regex("""[^\w.-]+"""), "_")
            .trim('_')
            .ifBlank { "hls_${System.currentTimeMillis()}" }
            .lowercase(Locale.US)
        var candidate = File(directory, "$baseName.$extension")
        var index = 1
        while (candidate.exists()) {
            candidate = File(directory, "${baseName}_$index.$extension")
            index++
        }
        return candidate
    }

    private fun fail(request: HlsDownloadRequest, message: String) {
        Log.e(DEBUG_TAG, "download failed id=${request.id} title=${request.title}: $message")
        val previous = HlsDownloadStore.retryProgress(request.id)
        update(
            HlsDownloadProgress(
                id = request.id,
                status = HlsDownloadStatus.FAILED,
                title = request.title,
                playlistUrl = request.playlistUrl,
                downloadedSegments = previous?.downloadedSegments ?: 0,
                totalSegments = previous?.totalSegments ?: 0,
                downloadedBytes = previous?.downloadedBytes ?: 0L,
                outputPath = previous?.outputPath,
                message = message,
                request = request
            )
        )
    }

    private fun update(progress: HlsDownloadProgress) {
        HlsDownloadStore.update(progress)
        val manager = getSystemService(Context.NOTIFICATION_SERVICE) as NotificationManager
        manager.notify(notificationIdFor(progress), buildNotification(progress))
    }

    private fun buildNotification(progress: HlsDownloadProgress) =
        NotificationCompat.Builder(this, channelIdFor(progress))
            .setSmallIcon(iconFor(progress))
            .setContentTitle(titleFor(progress))
            .setContentText(progress.message)
            .setContentIntent(
                PendingIntent.getActivity(
                    this,
                    0,
                    Intent(this, DownloadStatusActivity::class.java),
                    PendingIntent.FLAG_UPDATE_CURRENT or PendingIntent.FLAG_IMMUTABLE
                )
            )
            .setOngoing(
                progress.status == HlsDownloadStatus.DOWNLOADING ||
                    progress.status == HlsDownloadStatus.FETCHING_PLAYLIST ||
                    progress.status == HlsDownloadStatus.REMUXING
            )
            .setAutoCancel(progress.status == HlsDownloadStatus.COMPLETED || progress.status == HlsDownloadStatus.FAILED)
            .setPriority(if (progress.status == HlsDownloadStatus.FAILED) NotificationCompat.PRIORITY_HIGH else NotificationCompat.PRIORITY_LOW)
            .setProgress(progress.totalSegments, progress.downloadedSegments, progress.totalSegments == 0)
            .build()

    private fun notificationIdFor(progress: HlsDownloadProgress): Int =
        if (progress.status == HlsDownloadStatus.FAILED) {
            NOTIFICATION_ID_FAILURE_BASE + kotlin.math.abs(progress.id.hashCode() % 10_000)
        } else {
            NOTIFICATION_ID
        }

    private fun channelIdFor(progress: HlsDownloadProgress): String =
        if (progress.status == HlsDownloadStatus.FAILED) CHANNEL_ID_FAILURE else CHANNEL_ID

    private fun iconFor(progress: HlsDownloadProgress): Int =
        if (progress.status == HlsDownloadStatus.FAILED) android.R.drawable.stat_notify_error else android.R.drawable.stat_sys_download

    private fun titleFor(progress: HlsDownloadProgress): String =
        when (progress.status) {
            HlsDownloadStatus.FAILED -> "다운로드 실패: ${progress.title.ifBlank { "동영상" }}"
            HlsDownloadStatus.COMPLETED -> "다운로드 완료: ${progress.title.ifBlank { "동영상" }}"
            else -> progress.title.ifBlank { "다운로드" }
        }

    private fun createNotificationChannel() {
        if (Build.VERSION.SDK_INT < Build.VERSION_CODES.O) return
        val manager = getSystemService(Context.NOTIFICATION_SERVICE) as NotificationManager
        manager.createNotificationChannel(
            NotificationChannel(
                CHANNEL_ID,
                "동영상 다운로드",
                NotificationManager.IMPORTANCE_LOW
            )
        )
        manager.createNotificationChannel(
            NotificationChannel(
                CHANNEL_ID_FAILURE,
                "동영상 다운로드 실패",
                NotificationManager.IMPORTANCE_HIGH
            )
        )
    }

    companion object {
        const val ACTION_CANCEL = "com.kys.videomanager.hls.CANCEL"
        const val ACTION_CANCEL_ONE = "com.kys.videomanager.hls.CANCEL_ONE"
        const val ACTION_RETRY = "com.kys.videomanager.hls.RETRY"
        const val EXTRA_DOWNLOAD_ID = "download_id"
        private const val DEBUG_TAG = "DDDDD"
        private const val CHANNEL_ID = "hls_download"
        private const val CHANNEL_ID_FAILURE = "hls_download_failure"
        private const val NOTIFICATION_ID = 2001
        private const val NOTIFICATION_ID_FAILURE_BASE = 2100
        private const val CONNECT_TIMEOUT_MS = 15_000
        private const val READ_TIMEOUT_MS = 20_000
        private const val MAX_PLAYLIST_DEPTH = 3
        private val TRANSIENT_HTTP_CODES = setOf(408, 425, 429, 500, 502, 503, 504)

        fun start(context: Context, request: HlsDownloadRequest) {
            HlsDownloadStore.initialize(context.applicationContext)
            HlsDownloadStore.enqueue(request)
            val intent = Intent(context, HlsDownloadService::class.java)
            androidx.core.content.ContextCompat.startForegroundService(context, intent)
        }

        fun cancel(context: Context) {
            val intent = Intent(context, HlsDownloadService::class.java).apply {
                action = ACTION_CANCEL
            }
            context.startService(intent)
        }

        fun cancel(context: Context, id: String) {
            val intent = Intent(context, HlsDownloadService::class.java).apply {
                action = ACTION_CANCEL_ONE
                putExtra(EXTRA_DOWNLOAD_ID, id)
            }
            context.startService(intent)
        }

        fun retry(context: Context, id: String) {
            HlsDownloadStore.initialize(context.applicationContext)
            val intent = Intent(context, HlsDownloadService::class.java).apply {
                action = ACTION_RETRY
                putExtra(EXTRA_DOWNLOAD_ID, id)
            }
            androidx.core.content.ContextCompat.startForegroundService(context, intent)
        }
    }

    private fun cancelAllDownloads() {
        downloadJobs.values.forEach { it.cancel() }
        downloadJobs.clear()
        HlsDownloadStore.snapshot()
            .filter { it.status == HlsDownloadStatus.DOWNLOADING || it.status == HlsDownloadStatus.FETCHING_PLAYLIST || it.status == HlsDownloadStatus.REMUXING }
            .forEach { progress ->
                HlsDownloadStore.update(
                    progress.copy(
                        status = HlsDownloadStatus.CANCELED,
                        message = "다운로드를 일시 중단했습니다. 다시 시도하면 이어받습니다."
                    )
                )
            }
    }

    private fun cancelDownload(id: String?) {
        if (id.isNullOrBlank()) return
        downloadJobs.remove(id)?.cancel()
        HlsDownloadStore.snapshot()
            .firstOrNull { it.id == id }
            ?.let { progress ->
                HlsDownloadStore.update(
                    progress.copy(
                        status = HlsDownloadStatus.CANCELED,
                        message = "다운로드를 일시 중단했습니다. 다시 시도하면 이어받습니다."
                    )
                )
            }
        if (downloadJobs.isEmpty()) stopSelf()
    }

    private fun retryDownload(id: String?) {
        if (id.isNullOrBlank()) return
        val request = HlsDownloadStore.retryRequest(id) ?: return
        // A download waiting out its backoff delay still holds its coroutine job in
        // downloadJobs, so startDownload() would otherwise no-op against a manual retry.
        downloadJobs.remove(id)?.cancel()
        HlsDownloadStore.markRetryQueued(request)
        startForeground(NOTIFICATION_ID, buildNotification(HlsDownloadProgress(message = "다운로드 준비 중")))
        startDownload(request)
    }

    private fun deletePartialFiles(progress: HlsDownloadProgress) {
        runCatching {
            deletePartialTempFile(progress.id)
            progress.outputPath
                ?.takeIf { it.isNotBlank() }
                ?.let { File(it) }
                ?.takeIf { it.exists() && progress.status != HlsDownloadStatus.COMPLETED }
                ?.delete()
        }.onFailure { throwable ->
            Log.e(DEBUG_TAG, "failed to delete partial download: ${throwable.message}", throwable)
        }
    }

    private fun deletePartialTempFile(id: String) {
        File(cacheDir, "hls/$id.ts").delete()
    }
}
