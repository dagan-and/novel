package com.kys.videomanager.videotrim

import org.junit.Assert.assertEquals
import org.junit.Test

class VideoTrimValidationTest {

    @Test fun `valid trim request is accepted`() {
        val result = VideoTrimValidator.validate(
            startSeconds = 60L,
            endSeconds = 120L,
            videoDurationMs = 180_000L
        )

        assertEquals(VideoTrimValidationResult.Valid, result)
    }

    @Test fun `end time must be after start time`() {
        val result = VideoTrimValidator.validate(
            startSeconds = 120L,
            endSeconds = 60L,
            videoDurationMs = 180_000L
        )

        assertEquals(VideoTrimValidationResult.EndBeforeStart, result)
    }

    @Test fun `end time cannot exceed video duration tolerance`() {
        val result = VideoTrimValidator.validate(
            startSeconds = 10L,
            endSeconds = 130L,
            videoDurationMs = 120_000L
        )

        assertEquals(VideoTrimValidationResult.EndExceedsDuration, result)
    }

    @Test fun `zero length video still validates relative time order`() {
        val result = VideoTrimValidator.validate(
            startSeconds = 10L,
            endSeconds = 20L,
            videoDurationMs = 0L
        )

        assertEquals(VideoTrimValidationResult.Valid, result)
    }
}
