package com.kys.videomanager.hlsplaylist

import org.junit.Assert.assertEquals
import org.junit.Assert.assertTrue
import org.junit.Test

class HlsPageAnalyzerTest {

    @Test fun `playlist in page html is returned first`() {
        val result = HlsPageAnalyzer.analyze(
            pageUrl = "https://upload18.org/play/index/mkmp-748",
            html = """
                <html><script>var file = "https://cdn.example.com/hls/master.m3u8?token=abc";</script></html>
            """.trimIndent()
        )

        assertEquals("https://cdn.example.com/hls/master.m3u8?token=abc", result.playlistUrl)
        assertTrue(result.followUrls.isEmpty())
    }

    @Test fun `iframe and script urls are resolved against the page url`() {
        val result = HlsPageAnalyzer.analyze(
            pageUrl = "https://upload18.org/play/index/mkmp-748",
            html = """
                <iframe src="/embed/mkmp-748"></iframe>
                <script src="https://cdn.example.com/player.js"></script>
            """.trimIndent()
        )

        assertEquals(
            listOf(
                "https://upload18.org/embed/mkmp-748",
                "https://cdn.example.com/player.js"
            ),
            result.followUrls
        )
    }

    @Test fun `non media links are ignored`() {
        val result = HlsPageAnalyzer.analyze(
            pageUrl = "https://upload18.org/play/index/mkmp-748",
            html = """<a href="/terms">terms</a>"""
        )

        assertEquals(null, result.playlistUrl)
        assertTrue(result.followUrls.isEmpty())
    }
}
