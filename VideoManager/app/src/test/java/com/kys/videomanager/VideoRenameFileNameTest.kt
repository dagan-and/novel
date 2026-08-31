package com.kys.videomanager

import org.junit.Assert.assertEquals
import org.junit.Test

class VideoRenameFileNameTest {

    @Test fun `default edit text value is original name without extension`() {
        assertEquals("계단1", VideoRenameFileName.defaultEditableName("계단1.mp4"))
    }

    @Test fun `renamed output keeps original extension when user enters base name`() {
        assertEquals("계단1_편집본.mp4", VideoRenameFileName.outputName("계단1.mp4", "계단1_편집본"))
    }

    @Test fun `renamed output accepts explicit extension`() {
        assertEquals("계단1_편집본.mkv", VideoRenameFileName.outputName("계단1.mp4", "계단1_편집본.mkv"))
    }
}
