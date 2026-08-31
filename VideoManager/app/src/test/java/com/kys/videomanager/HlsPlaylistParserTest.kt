package com.kys.videomanager

import org.junit.Assert.assertEquals
import org.junit.Assert.assertFalse
import org.junit.Assert.assertTrue
import org.junit.Test

class HlsPlaylistParserTest {

    @Test fun `media playlist resolves relative segment urls`() {
        val playlist = """
            #EXTM3U
            #EXT-X-TARGETDURATION:6
            #EXTINF:5.0,
            seg-001.ts
            #EXTINF:5.0,
            ../seg-002.ts?token=abc
        """.trimIndent()

        val result = HlsPlaylistParser.parse("https://cdn.example.com/hls/master/playlist.m3u8", playlist)

        assertFalse(result.isMaster)
        assertFalse(result.isEncrypted)
        assertEquals(
            listOf(
                "https://cdn.example.com/hls/master/seg-001.ts",
                "https://cdn.example.com/hls/seg-002.ts?token=abc"
            ),
            result.segmentUrls
        )
    }

    @Test fun `master playlist selects highest bandwidth variant`() {
        val playlist = """
            #EXTM3U
            #EXT-X-STREAM-INF:BANDWIDTH=800000
            low/index.m3u8
            #EXT-X-STREAM-INF:BANDWIDTH=2200000
            high/index.m3u8
        """.trimIndent()

        val result = HlsPlaylistParser.parse("https://cdn.example.com/video/master.m3u8", playlist)

        assertTrue(result.isMaster)
        assertEquals("https://cdn.example.com/video/high/index.m3u8", result.variantUrl)
    }

    @Test fun `encrypted playlist is reported as unsupported`() {
        val playlist = """
            #EXTM3U
            #EXT-X-KEY:METHOD=AES-128,URI="key.key"
            #EXTINF:5.0,
            seg-001.ts
        """.trimIndent()

        val result = HlsPlaylistParser.parse("https://cdn.example.com/hls/playlist.m3u8", playlist)

        assertTrue(result.isEncrypted)
    }
}
