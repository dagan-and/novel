package com.kys.videomanager.ffmpeg
import com.kys.videomanager.videoimport.VideoImportOption
import com.kys.videomanager.videoimport.VideoImportPolicy

import org.junit.Assert.assertEquals
import org.junit.Assert.assertTrue
import org.junit.Test

class FfmpegImportCommandTest {

    @Test fun `hardware command targets 1080p without upscaling and selected bitrate`() {
        val policy = VideoImportPolicy.evaluate(
            height = 2160,
            bitrate = 8_000_000,
            option = VideoImportOption.compress(1_800_000)
        )

        val args = FfmpegImportCommand.hardware(
            inputPath = "/tmp/input.mov",
            outputPath = "/tmp/output.mp4",
            policy = policy
        )

        assertEquals("-y", args[0])
        assertTrue(args.contains("scale='if(gt(iw\\,ih)\\,-2\\,min(iw\\,1080))':'if(gt(iw\\,ih)\\,min(ih\\,1080)\\,-2)',format=nv12"))
        assertTrue(args.contains("hevc_mediacodec"))
        assertTrue(args.contains("hvc1"))
        assertTrue(args.contains("1800k"))
        assertEquals("/tmp/output.mp4", args.last())
    }

    @Test fun `software fallback uses fast x265 preset`() {
        val policy = VideoImportPolicy.evaluate(
            height = 720,
            bitrate = 4_000_000,
            option = VideoImportOption.compress(2_000_000)
        )

        val args = FfmpegImportCommand.softwareFallback(
            inputPath = "/tmp/input.mov",
            outputPath = "/tmp/output.mp4",
            policy = policy
        )

        assertTrue(args.contains("scale='if(gt(iw\\,ih)\\,-2\\,min(iw\\,720))':'if(gt(iw\\,ih)\\,min(ih\\,720)\\,-2)',format=nv12"))
        assertTrue(args.contains("libx265"))
        assertTrue(args.contains("hvc1"))
        assertTrue(args.contains("veryfast"))
        assertTrue(args.contains("2000k"))
    }

    @Test fun `scale filter limits the resolution basis instead of forcing output height`() {
        val policy = VideoImportPolicy.evaluate(
            width = 720,
            height = 1280,
            bitrate = 4_000_000,
            option = VideoImportOption.compress(2_000_000)
        )

        val args = FfmpegImportCommand.hardware(
            inputPath = "/tmp/input.mov",
            outputPath = "/tmp/output.mp4",
            policy = policy
        )

        assertTrue(args.contains("scale='if(gt(iw\\,ih)\\,-2\\,min(iw\\,720))':'if(gt(iw\\,ih)\\,min(ih\\,720)\\,-2)',format=nv12"))
    }
}
