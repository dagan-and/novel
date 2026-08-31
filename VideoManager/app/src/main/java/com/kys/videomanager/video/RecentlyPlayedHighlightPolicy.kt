package com.kys.videomanager.video

object RecentlyPlayedHighlightPolicy {
    fun isHighlighted(itemPath: String, lastPlayedPath: String?): Boolean =
        lastPlayedPath != null && itemPath == lastPlayedPath
}
