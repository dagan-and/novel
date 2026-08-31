package com.kys.videomanager

object VideoListFormatter {
    fun formatSize(bytes: Long): String =
        "%.1f GB".format(bytes / (1024.0 * 1024.0 * 1024.0))
}

enum class VideoSortMode(val label: String) {
    RATING_DESC("별점순"),
    NEWEST_FIRST("최신순"),
    OLDEST_FIRST("오래된순"),
    RANDOM("랜덤")
}

fun VideoItem.ratingPreferenceKey(): String = name
