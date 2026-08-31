package com.kys.videomanager

sealed class RatingFilter {
    object ALL : RatingFilter()
    object UNRATED : RatingFilter()
    data class Stars(val stars: Int) : RatingFilter()
}

fun RatingFilter.toPreferenceValue(): String =
    when (this) {
        RatingFilter.ALL -> "all"
        RatingFilter.UNRATED -> "unrated"
        is RatingFilter.Stars -> "stars:$stars"
    }

fun ratingFilterFromPreferenceValue(value: String?): RatingFilter {
    if (value == null) return RatingFilter.ALL
    return when {
        value == "all" -> RatingFilter.ALL
        value == "unrated" -> RatingFilter.UNRATED
        value.startsWith("stars:") -> {
            val stars = value.removePrefix("stars:").toIntOrNull()
            if (stars != null && stars in 1..5) RatingFilter.Stars(stars) else RatingFilter.ALL
        }
        else -> RatingFilter.ALL
    }
}

fun filterVideos(videos: List<VideoItem>, filter: RatingFilter): List<VideoItem> =
    when (filter) {
        RatingFilter.ALL     -> videos
        RatingFilter.UNRATED -> videos.filter { it.rating == 0f }
        is RatingFilter.Stars -> videos.filter {
            if (filter.stars == 5) it.rating == 5f
            else it.rating >= filter.stars.toFloat() && it.rating < (filter.stars + 1).toFloat()
        }
    }
