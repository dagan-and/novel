package com.kys.videomanager.videoimport

import org.junit.Assert.assertEquals
import org.junit.Test

class VideoImportQueueTest {

    @Test
    fun `import request queue round trips selected videos and options`() {
        VideoImportQueue.clearForTest()
        val request = VideoImportRequest(
            id = "import-1",
            option = VideoImportOption.compress(1_800_000),
            items = listOf(
                VideoImportItem(
                    uri = "content://media/video/1",
                    title = "holiday.mov",
                    width = 3840,
                    height = 2160,
                    bitrate = 8_000_000,
                    sizeBytes = 123_456_789L,
                    durationMs = 60_000L,
                    codecMime = "video/avc"
                )
            )
        )

        VideoImportQueue.enqueue(request)

        assertEquals(request, VideoImportQueue.dequeue())
        assertEquals(null, VideoImportQueue.dequeue())
    }

    @Test
    fun `import requests delete source by default unless caller preserves it`() {
        val defaultRequest = VideoImportRequest(
            id = "import-default",
            option = VideoImportOption.original,
            items = emptyList()
        )
        val preserveSourceRequest = defaultRequest.copy(deleteSourceAfterImport = false)

        assertEquals(true, defaultRequest.deleteSourceAfterImport)
        assertEquals(false, preserveSourceRequest.deleteSourceAfterImport)
    }
}
