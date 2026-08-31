package com.kys.videomanager

import java.net.URI

enum class SearchWebViewPrimaryAction {
    NONE,
    WATCH,
    PRODUCT_CODE_SEARCH
}

enum class SearchWebViewSecondaryAction {
    NONE,
    POSTER,
    DOWNLOAD
}

data class SearchWebViewButtonState(
    val primaryAction: SearchWebViewPrimaryAction,
    val secondaryAction: SearchWebViewSecondaryAction
)

object SearchWebViewButtonPolicy {
    fun resolve(currentUrl: String?, hasDetectedPlaylist: Boolean): SearchWebViewButtonState {
        return when {
            isDetailPage(currentUrl) -> SearchWebViewButtonState(
                primaryAction = SearchWebViewPrimaryAction.WATCH,
                secondaryAction = SearchWebViewSecondaryAction.POSTER
            )
            isUpload18PlayPage(currentUrl) && hasDetectedPlaylist -> SearchWebViewButtonState(
                primaryAction = SearchWebViewPrimaryAction.NONE,
                secondaryAction = SearchWebViewSecondaryAction.DOWNLOAD
            )
            else -> SearchWebViewButtonState(
                primaryAction = SearchWebViewPrimaryAction.PRODUCT_CODE_SEARCH,
                secondaryAction = SearchWebViewSecondaryAction.NONE
            )
        }
    }

    private fun isDetailPage(currentUrl: String?): Boolean {
        val uri = parseUri(currentUrl) ?: return false
        val segments = uri.pathSegments()
        return uri.normalizedHost() == "avdbapi.com" &&
            segments.size >= 2 &&
            segments[0] == "detail"
    }

    private fun isUpload18PlayPage(currentUrl: String?): Boolean {
        val uri = parseUri(currentUrl) ?: return false
        val segments = uri.pathSegments()
        return uri.normalizedHost() == "upload18.org" &&
            segments.size >= 3 &&
            segments[0] == "play" &&
            segments[1] == "index"
    }

    private fun parseUri(currentUrl: String?): URI? =
        if (currentUrl.isNullOrBlank()) {
            null
        } else {
            runCatching { URI(currentUrl) }.getOrNull()
        }

    private fun URI.normalizedHost(): String? =
        host?.removePrefix("www.")

    private fun URI.pathSegments(): List<String> =
        path
            ?.split("/")
            ?.filter { it.isNotBlank() }
            .orEmpty()
}
