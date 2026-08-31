package com.kys.videomanager.videoimport

import java.util.UUID

data class VideoImportItem(
    val uri: String,
    val title: String,
    val sizeBytes: Long? = null,
    val width: Int? = null,
    val height: Int? = null,
    val bitrate: Int? = null,
    val durationMs: Long? = null,
    val codecMime: String? = null
)

data class VideoImportRequest(
    val id: String = UUID.randomUUID().toString(),
    val option: VideoImportOption,
    val items: List<VideoImportItem>,
    val deleteSourceAfterImport: Boolean = true
)

object VideoImportQueue {
    private val pendingRequests = mutableListOf<VideoImportRequest>()

    fun enqueue(request: VideoImportRequest) {
        synchronized(pendingRequests) {
            pendingRequests += request
        }
    }

    fun dequeue(): VideoImportRequest? =
        synchronized(pendingRequests) {
            if (pendingRequests.isEmpty()) null else pendingRequests.removeAt(0)
        }

    fun clearForTest() {
        synchronized(pendingRequests) {
            pendingRequests.clear()
        }
    }
}
