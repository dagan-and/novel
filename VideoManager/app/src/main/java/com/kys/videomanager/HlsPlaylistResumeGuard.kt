package com.kys.videomanager

object HlsPlaylistResumeGuard {
    fun shouldRestartFromScratch(previousTotalSegments: Int, newTotalSegments: Int): Boolean =
        previousTotalSegments > 0 && newTotalSegments > 0 && previousTotalSegments != newTotalSegments
}
