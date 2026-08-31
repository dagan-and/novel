package com.kys.videomanager

import org.junit.Assert.assertEquals
import org.junit.Assert.assertFalse
import org.junit.Assert.assertTrue
import org.junit.Test

class VideoImportPolicyTest {

    @Test
    fun `videos over 1080p should be compressed`() {
        val policy = VideoImportPolicy.evaluate(
            height = 2160,
            bitrate = 8_000_000,
            option = VideoImportOption.compress()
        )

        assertTrue(policy.shouldCompress)
        assertEquals(1080, policy.targetHeight)
        assertEquals(1_500_000, policy.targetBitrate)
    }

    @Test
    fun `compression option copies videos already under target quality`() {
        val policy = VideoImportPolicy.evaluate(height = 360, bitrate = 600_000, option = VideoImportOption.compress())

        assertFalse(policy.shouldCompress)
    }

    @Test
    fun `compression option compresses high bitrate videos without upscaling`() {
        val fullHd = VideoImportPolicy.evaluate(height = 1080, bitrate = 8_000_000, option = VideoImportOption.compress())
        val hd = VideoImportPolicy.evaluate(height = 720, bitrate = 3_000_000, option = VideoImportOption.compress())

        assertTrue(fullHd.shouldCompress)
        assertEquals(1080, fullHd.targetHeight)
        assertTrue(hd.shouldCompress)
        assertEquals(720, hd.targetHeight)
    }

    @Test
    fun `portrait videos under 1080p compress at their original resolution basis`() {
        val preview = VideoImportPreview.create(
            name = "portrait.mp4",
            width = 720,
            height = 1280,
            bitrate = 3_000_000,
            sizeBytes = 80L * 1024L * 1024L,
            option = VideoImportOption.compress()
        )

        assertTrue(preview.policy.shouldCompress)
        assertEquals(720, preview.policy.targetHeight)
    }

    @Test
    fun `unknown resolution should be copied as-is`() {
        assertFalse(VideoImportPolicy.evaluate(height = null, bitrate = null, option = VideoImportOption.compress()).shouldCompress)
    }

    @Test
    fun `original option always copies as-is`() {
        assertFalse(VideoImportPolicy.evaluate(height = 2160, bitrate = 20_000_000, option = VideoImportOption.original).shouldCompress)
    }

    @Test
    fun `compression option keeps 1080p while custom bitrate changes`() {
        val policy = VideoImportPolicy.evaluate(height = 2160, bitrate = 10_000_000, option = VideoImportOption.compress(1_800_000))

        assertTrue(policy.shouldCompress)
        assertEquals(1080, policy.targetHeight)
        assertEquals(1_800_000, policy.targetBitrate)
    }

    @Test
    fun `quality status identifies high quality videos`() {
        val status = VideoQualityStatus.evaluate(width = 3840, height = 2160, bitrate = 18_000_000)

        assertEquals(VideoQualityStatus.HIGH_QUALITY, status)
    }

    @Test
    fun `quality status identifies lightweight videos`() {
        val status = VideoQualityStatus.evaluate(width = 1280, height = 720, bitrate = 900_000)

        assertEquals(VideoQualityStatus.LIGHTWEIGHT, status)
    }

    @Test
    fun `import preview explains compression decision`() {
        val preview = VideoImportPreview.create(
            name = "clip.mp4",
            width = 3840,
            height = 2160,
            bitrate = 18_000_000,
            sizeBytes = 100L * 1024L * 1024L,
            option = VideoImportOption.compress()
        )

        assertTrue(preview.policy.shouldCompress)
        assertEquals(VideoQualityStatus.HIGH_QUALITY, preview.qualityStatus)
        assertEquals("압축됨", preview.actionLabel)
    }

    @Test
    fun `codec mime types map to readable labels`() {
        assertEquals("H.264 (AVC)", VideoCodecName.fromMime("video/avc"))
        assertEquals("H.265 (HEVC)", VideoCodecName.fromMime("video/hevc"))
        assertEquals("VP9", VideoCodecName.fromMime("video/x-vnd.on2.vp9"))
        assertEquals("코덱 정보 없음", VideoCodecName.fromMime(null))
        assertEquals("XYZ", VideoCodecName.fromMime("video/xyz"))
    }

    @Test
    fun `display name is preferred and sanitized`() {
        val name = VideoImportFileName.choose(
            displayName = "family/video:party.mov",
            mediaStoreName = "1001112.mp4",
            fallbackSegment = "document/1234",
            timestampMillis = 1_704_067_200_000L
        )

        assertEquals("family_video_party.mov", name)
    }

    @Test
    fun `generated numeric picker names are replaced with a stable Meet name`() {
        val name = VideoImportFileName.choose(
            displayName = "1001112.mp4",
            mediaStoreName = null,
            fallbackSegment = "video/1001112",
            timestampMillis = 1_704_067_200_000L
        )

        assertEquals("Meet_20240101_090000.mp4", name)
    }

    @Test
    fun `compressed output only changes extension to mp4`() {
        val name = VideoImportFileName.compressedOutputName("holiday.mov")

        assertEquals("holiday.mp4", name)
    }

    @Test
    fun `import preview estimates compressed size from duration and selected bitrate`() {
        val preview = VideoImportPreview.create(
            name = "clip.mov",
            width = 3840,
            height = 2160,
            bitrate = 18_000_000,
            sizeBytes = 300L * 1024L * 1024L,
            durationMs = 120_000L,
            option = VideoImportOption.compress(1_800_000)
        )

        assertEquals(28_920_000L, preview.estimatedOutputSizeBytes)
    }

    @Test
    fun `import preview keeps original size estimate when copied as-is`() {
        val preview = VideoImportPreview.create(
            name = "clip.mp4",
            width = 1280,
            height = 720,
            bitrate = 900_000,
            sizeBytes = 20L * 1024L * 1024L,
            durationMs = 90_000L,
            option = VideoImportOption.compress(2_500_000)
        )

        assertEquals(20L * 1024L * 1024L, preview.estimatedOutputSizeBytes)
    }
}
