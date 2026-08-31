package com.kys.videomanager

import org.junit.Assert.assertEquals
import org.junit.Test

class SearchWebViewButtonPolicyTest {
    @Test
    fun detailPageShowsWatchAndPosterButNoDownload() {
        val state = SearchWebViewButtonPolicy.resolve(
            currentUrl = "https://avdbapi.com/detail/fc2-ppv-4965833/",
            hasDetectedPlaylist = true
        )

        assertEquals(SearchWebViewPrimaryAction.WATCH, state.primaryAction)
        assertEquals(SearchWebViewSecondaryAction.POSTER, state.secondaryAction)
    }

    @Test
    fun playPageShowsDownloadOnlyAfterPlaylistDetected() {
        val beforeDetection = SearchWebViewButtonPolicy.resolve(
            currentUrl = "https://upload18.org/play/index/fc2-ppv-4965833",
            hasDetectedPlaylist = false
        )
        val afterDetection = SearchWebViewButtonPolicy.resolve(
            currentUrl = "https://upload18.org/play/index/fc2-ppv-4965833",
            hasDetectedPlaylist = true
        )

        assertEquals(SearchWebViewPrimaryAction.PRODUCT_CODE_SEARCH, beforeDetection.primaryAction)
        assertEquals(SearchWebViewSecondaryAction.NONE, beforeDetection.secondaryAction)
        assertEquals(SearchWebViewPrimaryAction.NONE, afterDetection.primaryAction)
        assertEquals(SearchWebViewSecondaryAction.DOWNLOAD, afterDetection.secondaryAction)
    }

    @Test
    fun idleSearchPageShowsProductCodeSearchButton() {
        val state = SearchWebViewButtonPolicy.resolve(
            currentUrl = "https://avdbapi.com",
            hasDetectedPlaylist = false
        )

        assertEquals(SearchWebViewPrimaryAction.PRODUCT_CODE_SEARCH, state.primaryAction)
        assertEquals(SearchWebViewSecondaryAction.NONE, state.secondaryAction)
    }
}
