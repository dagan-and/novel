package com.kys.videomanager

import org.junit.Assert.assertFalse
import org.junit.Assert.assertTrue
import org.junit.Test
import kotlin.io.path.createTempFile

class VideoTrimOutputValidatorTest {

    @Test fun `missing output is rejected`() {
        val file = createTempFile(prefix = "trim-output", suffix = ".mp4").toFile()
        file.delete()

        assertFalse(VideoTrimOutputValidator.isUsable(file))
    }

    @Test fun `empty output is rejected`() {
        val file = createTempFile(prefix = "trim-output", suffix = ".mp4").toFile()

        assertFalse(VideoTrimOutputValidator.isUsable(file))
        file.delete()
    }

    @Test fun `non empty output is accepted`() {
        val file = createTempFile(prefix = "trim-output", suffix = ".mp4").toFile()
        file.writeText("video")

        assertTrue(VideoTrimOutputValidator.isUsable(file))
        file.delete()
    }
}
