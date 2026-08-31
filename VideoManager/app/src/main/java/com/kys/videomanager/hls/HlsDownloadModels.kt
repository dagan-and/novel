package com.kys.videomanager.hls

import android.content.Context
import android.util.Log
import java.io.File
import java.util.concurrent.CopyOnWriteArraySet

data class HlsDownloadRequest(
    val id: String,
    val playlistUrl: String,
    val pageUrl: String?,
    val requestHeaders: Map<String, String>,
    val cookie: String?,
    val title: String
)

enum class HlsDownloadStatus {
    IDLE,
    FETCHING_PLAYLIST,
    DOWNLOADING,
    REMUXING,
    COMPLETED,
    FAILED,
    CANCELED
}

data class HlsDownloadProgress(
    val id: String = "",
    val status: HlsDownloadStatus = HlsDownloadStatus.IDLE,
    val title: String = "",
    val playlistUrl: String = "",
    val downloadedSegments: Int = 0,
    val totalSegments: Int = 0,
    val downloadedBytes: Long = 0L,
    val outputPath: String? = null,
    val message: String = "대기 중",
    val request: HlsDownloadRequest? = null
) {
    val percent: Int
        get() = if (totalSegments <= 0) 0 else (downloadedSegments * 100 / totalSegments).coerceIn(0, 100)
}

object HlsDownloadStore {
    private val progresses = linkedMapOf<String, HlsDownloadProgress>()
    private val pendingRequests = mutableListOf<HlsDownloadRequest>()

    private val listeners = CopyOnWriteArraySet<(List<HlsDownloadProgress>) -> Unit>()
    private var historyFile: File? = null
    private var initialized = false

    fun initialize(context: Context) {
        synchronized(progresses) {
            if (initialized) return
            historyFile = File(context.filesDir, HISTORY_FILE_NAME)
            val restored = runCatching {
                historyFile
                    ?.takeIf { it.exists() }
                    ?.readText()
                    ?.let(HlsDownloadHistoryCodec::decode)
                    .orEmpty()
            }.onFailure { throwable ->
                Log.e(DEBUG_TAG, "failed to load download history: ${throwable.message}", throwable)
            }.getOrDefault(emptyList())
            progresses.clear()
            restored.forEach { progress ->
                progresses[progress.id] = progress.asInterruptedIfRunning()
            }
            initialized = true
        }
        persistQuietly()
        notifyListeners()
    }

    fun update(progress: HlsDownloadProgress) {
        synchronized(progresses) {
            val previous = progresses[progress.id]
            progresses[progress.id] = progress.withResumableFieldsFrom(previous)
        }
        persistQuietly()
        notifyListeners()
    }

    fun snapshot(): List<HlsDownloadProgress> =
        synchronized(progresses) { progresses.values.toList() }

    fun remove(id: String) {
        synchronized(progresses) { progresses.remove(id) }
        persistQuietly()
        notifyListeners()
    }

    fun listen(listener: (List<HlsDownloadProgress>) -> Unit): () -> Unit {
        listeners += listener
        listener(snapshot())
        return { listeners -= listener }
    }

    fun enqueue(request: HlsDownloadRequest) {
        synchronized(pendingRequests) {
            pendingRequests += request
        }
        update(
            HlsDownloadProgress(
                id = request.id,
                status = HlsDownloadStatus.IDLE,
                title = request.title,
                playlistUrl = request.playlistUrl,
                message = "다운로드 대기 중",
                request = request
            )
        )
    }

    fun dequeue(): HlsDownloadRequest? =
        synchronized(pendingRequests) {
            if (pendingRequests.isEmpty()) null else pendingRequests.removeAt(0)
        }

    fun clearForTest() {
        synchronized(progresses) { progresses.clear() }
        synchronized(pendingRequests) { pendingRequests.clear() }
        historyFile = null
        initialized = false
        notifyListeners()
    }

    fun retryRequest(id: String): HlsDownloadRequest? =
        synchronized(progresses) { progresses[id]?.request }

    fun retryProgress(id: String): HlsDownloadProgress? =
        synchronized(progresses) { progresses[id] }

    fun markRetryQueued(request: HlsDownloadRequest) {
        synchronized(progresses) {
            val previous = progresses[request.id]
            progresses[request.id] = HlsDownloadProgress(
                id = request.id,
                status = HlsDownloadStatus.IDLE,
                title = request.title,
                playlistUrl = request.playlistUrl,
                downloadedSegments = previous?.downloadedSegments ?: 0,
                totalSegments = previous?.totalSegments ?: 0,
                downloadedBytes = previous?.downloadedBytes ?: 0L,
                outputPath = previous?.outputPath,
                message = "다운로드 재시도 대기 중",
                request = request
            )
        }
        persistQuietly()
        notifyListeners()
    }

    fun configureHistoryFileForTest(file: File) {
        synchronized(progresses) {
            historyFile = file
            initialized = true
        }
    }

    private fun notifyListeners() {
        val snapshot = snapshot()
        listeners.forEach { listener -> listener(snapshot) }
    }

    private fun persistQuietly() {
        val file = historyFile ?: return
        val snapshot = snapshot()
        runCatching {
            file.parentFile?.mkdirs()
            file.writeText(HlsDownloadHistoryCodec.encode(snapshot))
        }.onFailure { throwable ->
            Log.e(DEBUG_TAG, "failed to save download history: ${throwable.message}", throwable)
        }
    }

    private fun HlsDownloadProgress.asInterruptedIfRunning(): HlsDownloadProgress =
        if (isRunningStatus(status)) {
            copy(status = HlsDownloadStatus.FAILED, message = "앱이 종료되어 다운로드가 중단되었습니다.")
        } else {
            this
        }

    private fun HlsDownloadProgress.withResumableFieldsFrom(previous: HlsDownloadProgress?): HlsDownloadProgress {
        if (previous == null) return this
        return copy(
            downloadedSegments = if (downloadedSegments == 0) previous.downloadedSegments else downloadedSegments,
            totalSegments = if (totalSegments == 0) previous.totalSegments else totalSegments,
            downloadedBytes = if (downloadedBytes == 0L) previous.downloadedBytes else downloadedBytes,
            outputPath = outputPath ?: previous.outputPath,
            request = request ?: previous.request
        )
    }

    private fun isRunningStatus(status: HlsDownloadStatus): Boolean =
        status == HlsDownloadStatus.FETCHING_PLAYLIST ||
            status == HlsDownloadStatus.DOWNLOADING ||
            status == HlsDownloadStatus.REMUXING

    private const val HISTORY_FILE_NAME = "hls_download_history.json"
    private const val DEBUG_TAG = "DDDDD"
}
