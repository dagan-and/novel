package com.kys.videomanager

import org.junit.Assert.assertEquals
import org.junit.Assert.assertNull
import org.junit.Assert.assertTrue
import org.junit.Test

class SearchLinkFormatterTest {

    @Test fun `detail page url is converted to upload18 play index url`() {
        val result = SearchLinkFormatter.toUpload18Url("https://avdbapi.com/detail/mkmp-748/")

        assertEquals("https://upload18.org/play/index/mkmp-748", result)
    }

    @Test fun `detail page url without trailing slash is converted`() {
        val result = SearchLinkFormatter.toUpload18Url("https://avdbapi.com/detail/mkmp-748")

        assertEquals("https://upload18.org/play/index/mkmp-748", result)
    }

    @Test fun `non detail url cannot be converted`() {
        assertNull(SearchLinkFormatter.toUpload18Url("https://avdbapi.com/search?q=mkmp-748"))
    }

    @Test fun `other host cannot be converted`() {
        assertNull(SearchLinkFormatter.toUpload18Url("https://example.com/detail/mkmp-748/"))
    }

    @Test fun `detail page url is converted to upload18 poster image url`() {
        val result = SearchLinkFormatter.toPosterImageUrl("https://avdbapi.com/detail/mkmp-748/")

        assertEquals(
            "https://upload18.cc/v/MKMP-748/poster.jpg",
            result
        )
    }

    @Test fun `lowercase detail page code is uppercased for poster image url`() {
        val result = SearchLinkFormatter.toPosterImageUrl("https://avdbapi.com/detail/nhdtc-242/")

        assertEquals(
            "https://upload18.cc/v/NHDTC-242/poster.jpg",
            result
        )
    }

    @Test fun `non detail url cannot be converted to poster image url`() {
        assertNull(SearchLinkFormatter.toPosterImageUrl("https://avdbapi.com/search?q=mkmp-748"))
    }

    @Test fun `poster viewer html centers the poster image in the viewport`() {
        val result = SearchLinkFormatter.toPosterViewerHtml("https://upload18.cc/v/NHDTC-242/poster.jpg")

        assertTrue(result.contains("display:flex"))
        assertTrue(result.contains("align-items:center"))
        assertTrue(result.contains("justify-content:center"))
        assertTrue(result.contains("""src="https://upload18.cc/v/NHDTC-242/poster.jpg""""))
    }

    @Test fun `poster viewer html allows pinch zoom`() {
        val result = SearchLinkFormatter.toPosterViewerHtml("https://upload18.cc/v/NHDTC-242/poster.jpg")

        assertTrue(result.contains("user-scalable=yes"))
        assertTrue(result.contains("maximum-scale=5.0"))
    }
}
