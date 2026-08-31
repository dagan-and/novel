package com.kys.videomanager.ffmpeg

import org.junit.Assert.assertFalse
import org.junit.Assert.assertTrue
import org.junit.Test

class FfmpegRuntimeAvailabilityTest {

    @Test fun `native linkage failures are treated as ffmpeg unavailable`() {
        assertTrue(FfmpegRuntimeAvailability.isUnavailable(UnsatisfiedLinkError("ffmpeg")))
        assertTrue(FfmpegRuntimeAvailability.isUnavailable(NoClassDefFoundError("com/arthenica/ffmpegkit/FFmpegKit")))
        assertTrue(FfmpegRuntimeAvailability.isUnavailable(ExceptionInInitializerError("native init")))
    }

    @Test fun `ordinary command failures are not treated as ffmpeg unavailable`() {
        assertFalse(FfmpegRuntimeAvailability.isUnavailable(IllegalStateException("encoder failed")))
        assertFalse(FfmpegRuntimeAvailability.isUnavailable(RuntimeException("bad input")))
    }
}
