package com.kys.videomanager.search

import org.junit.Assert.assertEquals
import org.junit.Assert.assertNull
import org.junit.Test

class SearchPosterDisplayPolicyTest {
    @Test fun `detail page poster opens as popup so search webview history is preserved`() {
        val display = SearchPosterDisplayPolicy.resolve("https://avdbapi.com/detail/fc2-ppv-4965833/")

        assertEquals(
            SearchPosterDisplay.POPUP,
            display?.display
        )
        assertEquals(
            "https://upload18.cc/v/FC2-PPV-4965833/poster.jpg",
            display?.posterUrl
        )
    }

    @Test fun `non detail page has no poster popup`() {
        assertNull(SearchPosterDisplayPolicy.resolve("https://avdbapi.com"))
    }
}
