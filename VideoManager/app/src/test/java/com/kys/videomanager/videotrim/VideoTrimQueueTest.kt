package com.kys.videomanager.videotrim

import org.junit.Assert.assertEquals
import org.junit.Assert.assertNull
import org.junit.Test

class VideoTrimQueueTest {

    @Test fun `queued trim request is dequeued once`() {
        VideoTrimQueue.clearForTest()
        val request = VideoTrimRequest(
            inputPath = "/videos/input.mp4",
            outputName = "input_highlight.mp4",
            startSeconds = 15L,
            endSeconds = 60L
        )

        VideoTrimQueue.enqueue(request)

        assertEquals(request, VideoTrimQueue.dequeue())
        assertNull(VideoTrimQueue.dequeue())
    }
}
