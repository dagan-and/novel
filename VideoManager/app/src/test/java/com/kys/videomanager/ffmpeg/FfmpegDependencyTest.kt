package com.kys.videomanager.ffmpeg

import org.junit.Assert.assertTrue
import org.junit.Test
import java.nio.file.Files
import java.nio.file.Path
import java.nio.file.Paths

class FfmpegDependencyTest {

    @Test fun `ffmpeg kit runtime dependencies are declared explicitly`() {
        val buildFile = String(Files.readAllBytes(buildGradlePath()))

        assertTrue(buildFile.contains("dev.ffmpegkit-maintained:ffmpeg-kit-full-gpl:8.1.7"))
        assertTrue(buildFile.contains("com.arthenica:smart-exception-java:0.2.1"))
    }

    private fun buildGradlePath(): Path {
        val candidates = listOf(
            Paths.get("app/build.gradle"),
            Paths.get("build.gradle")
        )
        return candidates.firstOrNull { Files.exists(it) }
            ?: error("Missing app build.gradle")
    }
}
