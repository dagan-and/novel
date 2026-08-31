package com.kys.videomanager

data class VideoTrimRequest(
    val inputPath: String,
    val outputName: String,
    val startSeconds: Long,
    val endSeconds: Long
)

object VideoTrimQueue {
    private val pendingRequests = mutableListOf<VideoTrimRequest>()

    fun enqueue(request: VideoTrimRequest) {
        synchronized(pendingRequests) {
            pendingRequests += request
        }
    }

    fun dequeue(): VideoTrimRequest? =
        synchronized(pendingRequests) {
            if (pendingRequests.isEmpty()) null else pendingRequests.removeAt(0)
        }

    fun clearForTest() {
        synchronized(pendingRequests) {
            pendingRequests.clear()
        }
    }
}
