package com.kys.videomanager

import org.junit.Assert.assertEquals
import org.junit.Assert.assertNull
import org.junit.Test

class HlsDownloadHistoryCodecTest {
    @Test
    fun roundTripsProgressWithRetryRequest() {
        val request = HlsDownloadRequest(
            id = "one",
            playlistUrl = "https://example.com/video.m3u8",
            pageUrl = "https://example.com/page",
            requestHeaders = mapOf("User-Agent" to "agent", "Referer" to "ref"),
            cookie = "a=b",
            title = "video"
        )
        val progress = HlsDownloadProgress(
            id = "one",
            status = HlsDownloadStatus.FAILED,
            title = "video",
            playlistUrl = request.playlistUrl,
            downloadedSegments = 2,
            totalSegments = 10,
            downloadedBytes = 1234L,
            outputPath = "/storage/emulated/0/Download/VideoManager/video.ts",
            message = "다운로드 실패",
            request = request
        )

        val restored = HlsDownloadHistoryCodec.decode(HlsDownloadHistoryCodec.encode(listOf(progress)))

        assertEquals(listOf(progress), restored)
        assertEquals("agent", restored.first().request?.requestHeaders?.get("User-Agent"))
    }

    @Test
    fun decodeSkipsInvalidRowsInsteadOfThrowing() {
        val restored = HlsDownloadHistoryCodec.decode(
            """{"downloads":[{"id":7},{"id":"ok","status":"COMPLETED","title":"ok","playlistUrl":"u","message":"done"}]}"""
        )

        assertEquals(1, restored.size)
        assertEquals("ok", restored.first().id)
        assertNull(restored.first().request)
    }
}
