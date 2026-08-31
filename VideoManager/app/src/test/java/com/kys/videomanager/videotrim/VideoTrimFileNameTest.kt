package com.kys.videomanager.videotrim

import org.junit.Assert.assertEquals
import org.junit.Test

class VideoTrimFileNameTest {

    @Test fun `default edit text value is original name without extension`() {
        assertEquals("강아지", VideoTrimFileName.defaultEditableName("강아지.mp4"))
    }

    @Test fun `output name keeps original extension when user enters base name`() {
        assertEquals("강아지_하이라이트.mp4", VideoTrimFileName.outputName("강아지.mp4", "강아지_하이라이트"))
    }

    @Test fun `output name accepts explicit extension`() {
        assertEquals("강아지_하이라이트.mkv", VideoTrimFileName.outputName("강아지.mp4", "강아지_하이라이트.mkv"))
    }
}
