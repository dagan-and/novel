package com.kys.videomanager.hlsplaylist
import com.kys.videomanager.search.SearchWebViewController

import org.junit.Assert.assertEquals
import org.junit.Assert.assertFalse
import org.junit.Assert.assertNull
import org.junit.Assert.assertTrue
import org.junit.Test

class HlsRequestProbeTest {

    @Test fun `playlist content type returns request url`() {
        val result = HlsRequestProbe.detect(
            HlsProbeResponse(
                requestUrl = "https://cdn.example.com/stream/master",
                contentType = "application/vnd.apple.mpegurl; charset=utf-8",
                body = "#EXTM3U\n#EXT-X-STREAM-INF:BANDWIDTH=1000"
            )
        )

        assertEquals("https://cdn.example.com/stream/master", result?.playlistUrl)
        assertEquals("content-type", result?.reason)
    }

    @Test fun `playlist url is extracted from response body`() {
        val result = HlsRequestProbe.detect(
            HlsProbeResponse(
                requestUrl = "https://upload18.org/play/index/nhdtc-242",
                contentType = "text/html; charset=utf-8",
                body = """jwplayer().setup({ file: "https:\/\/cdn.example.com\/hls\/master.m3u8?token=abc" });"""
            )
        )

        assertEquals("https://cdn.example.com/hls/master.m3u8?token=abc", result?.playlistUrl)
        assertEquals("body", result?.reason)
    }

    @Test fun `non hls response returns null`() {
        val result = HlsRequestProbe.detect(
            HlsProbeResponse(
                requestUrl = "https://upload18.org/play/index/nhdtc-242",
                contentType = "text/html",
                body = "<html>No stream here</html>"
            )
        )

        assertNull(result)
    }

    @Test fun `static images are skipped but scripts and pages are inspectable`() {
        assertFalse(HlsRequestProbe.shouldInspectRequest("https://cdn.example.com/poster.jpg"))
        assertFalse(HlsRequestProbe.shouldInspectRequest("data:text/plain,hello"))
        assertTrue(HlsRequestProbe.shouldInspectRequest("https://upload18.org/player/js/player-init.min.js?v=2.1"))
        assertTrue(HlsRequestProbe.shouldInspectRequest("https://upload18.org/play/index/nhdtc-242"))
    }

    @Test fun `headers preserve browser context and add cookie referer user agent`() {
        val headers = HlsRequestProbe.buildHeaders(
            HlsProbeRequest(
                url = "https://upload18.org/play/index/nhdtc-242",
                pageUrl = "https://upload18.org/play/index/nhdtc-242",
                requestHeaders = mapOf("Accept" to "*/*"),
                cookie = "session=abc"
            )
        )

        assertEquals("*/*", headers["Accept"])
        assertEquals("session=abc", headers["Cookie"])
        assertEquals("https://upload18.org/play/index/nhdtc-242", headers["Referer"])
        assertEquals(SearchWebViewController.WEB_USER_AGENT, headers["User-Agent"])
    }

    @Test fun `headers force identity encoding even if browser requested compression`() {
        val headers = HlsRequestProbe.buildHeaders(
            HlsProbeRequest(
                url = "https://upload18.org/play/index/nhdtc-242",
                pageUrl = null,
                requestHeaders = mapOf("Accept-Encoding" to "gzip, deflate, br"),
                cookie = null
            )
        )

        assertEquals("identity", headers["Accept-Encoding"])
    }
}
