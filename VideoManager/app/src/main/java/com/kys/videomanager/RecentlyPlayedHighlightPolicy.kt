package com.kys.videomanager

object RecentlyPlayedHighlightPolicy {
    fun isHighlighted(itemPath: String, lastPlayedPath: String?): Boolean =
        lastPlayedPath != null && itemPath == lastPlayedPath
}
