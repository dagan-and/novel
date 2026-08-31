package com.kys.videomanager.hlsplaylist

import org.junit.Assert.assertFalse
import org.junit.Assert.assertTrue
import org.junit.Test

class HlsStreamDetectorTest {

    @Test fun `m3u8 playlist url is detected`() {
        assertTrue(HlsStreamDetector.isPlaylistUrl("https://cdn.example.com/video/master.m3u8"))
    }

    @Test fun `m3u8 playlist url with query is detected`() {
        assertTrue(HlsStreamDetector.isPlaylistUrl("https://cdn.example.com/video/index.m3u8?token=abc123"))
    }

    @Test fun `segment and page urls are ignored`() {
        assertFalse(HlsStreamDetector.isPlaylistUrl("https://cdn.example.com/video/segment001.ts"))
        assertFalse(HlsStreamDetector.isPlaylistUrl("https://upload18.org/play/index/mkmp-748"))
    }

    @Test fun `playlist url can be extracted from javascript text`() {
        val result = HlsStreamDetector.extractPlaylistUrl(
            "player.load('https://cdn.example.com/hls/master.m3u8?token=abc123');"
        )

        assertTrue(result == "https://cdn.example.com/hls/master.m3u8?token=abc123")
    }

    @Test fun `escaped playlist url can be extracted from javascript text`() {
        val result = HlsStreamDetector.extractPlaylistUrl(
            """player.load("https:\/\/cdn.example.com\/hls\/master.m3u8?token=abc123");"""
        )

        assertTrue(result == "https://cdn.example.com/hls/master.m3u8?token=abc123")
    }

    @Test fun `non playlist text returns null`() {
        val result = HlsStreamDetector.extractPlaylistUrl(
            "player.load('https://cdn.example.com/hls/segment001.ts');"
        )

        assertTrue(result == null)
    }
}
