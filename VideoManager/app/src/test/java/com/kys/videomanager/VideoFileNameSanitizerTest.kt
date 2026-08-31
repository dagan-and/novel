package com.kys.videomanager

import org.junit.Assert.assertEquals
import org.junit.Test

class VideoFileNameSanitizerTest {

    @Test fun `unsafe filename characters are replaced with spaces`() {
        assertEquals(
            "강아지 하이라이트 1",
            VideoFileNameSanitizer.sanitizeBaseName(" 강아지/하이라이트:1? ")
        )
    }

    @Test fun `blank sanitized filename falls back to provided name`() {
        assertEquals(
            "강아지",
            VideoFileNameSanitizer.sanitizeBaseName("///???", fallback = "강아지")
        )
    }

    @Test fun `trim output name sanitizes base name and keeps original extension`() {
        assertEquals(
            "강아지 하이라이트.mp4",
            VideoTrimFileName.outputName("원본.mp4", "강아지/하이라이트")
        )
    }

    @Test fun `rename output name sanitizes explicit extension separately`() {
        assertEquals(
            "강아지 하이라이트.mkv",
            VideoRenameFileName.outputName("원본.mp4", "강아지:하이라이트.mkv")
        )
    }
}
