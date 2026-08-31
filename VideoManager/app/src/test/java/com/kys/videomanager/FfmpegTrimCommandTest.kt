package com.kys.videomanager

import org.junit.Assert.assertArrayEquals
import org.junit.Test

class FfmpegTrimCommandTest {

    @Test fun `fast trim copies streams between start and duration`() {
        val args = FfmpegTrimCommand.fastCopy(
            inputPath = "/tmp/input.mp4",
            outputPath = "/tmp/output.mp4",
            startSeconds = 956L,
            endSeconds = 4879L
        )

        assertArrayEquals(
            arrayOf(
                "-y",
                "-ss", "00:15:56",
                "-i", "/tmp/input.mp4",
                "-t", "01:05:23",
                "-c", "copy",
                "-avoid_negative_ts", "make_zero",
                "/tmp/output.mp4"
            ),
            args
        )
    }
}
