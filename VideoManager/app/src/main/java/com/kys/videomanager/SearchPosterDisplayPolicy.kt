package com.kys.videomanager

enum class SearchPosterDisplay {
    POPUP
}

data class SearchPosterDisplayState(
    val display: SearchPosterDisplay,
    val posterUrl: String
)

object SearchPosterDisplayPolicy {
    fun resolve(currentUrl: String?): SearchPosterDisplayState? {
        val posterUrl = SearchLinkFormatter.toPosterImageUrl(currentUrl) ?: return null
        return SearchPosterDisplayState(
            display = SearchPosterDisplay.POPUP,
            posterUrl = posterUrl
        )
    }
}
