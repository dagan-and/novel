package com.kys.videomanager.videotrim

import org.junit.Assert.assertEquals
import org.junit.Assert.assertNull
import org.junit.Test

class VideoTrimTimeTest {

    @Test fun `parses minute second input as seconds`() {
        assertEquals(956L, VideoTrimTime.parseSeconds("15:56"))
    }

    @Test fun `parses hour minute second input as seconds`() {
        assertEquals(4879L, VideoTrimTime.parseSeconds("1:21:19"))
    }

    @Test fun `parses compact numeric input as time from the right`() {
        assertEquals(956L, VideoTrimTime.parseSeconds("1556"))
        assertEquals(360L, VideoTrimTime.parseSeconds("000600"))
        assertEquals(4879L, VideoTrimTime.parseSeconds("12119"))
    }

    @Test fun `formats seconds as ffmpeg timestamp`() {
        assertEquals("01:05:23", VideoTrimTime.formatTimestamp(3923L))
    }

    @Test fun `rejects empty and malformed input`() {
        assertNull(VideoTrimTime.parseSeconds(""))
        assertNull(VideoTrimTime.parseSeconds("1:2:3:4"))
        assertNull(VideoTrimTime.parseSeconds("12:xx"))
        assertNull(VideoTrimTime.parseSeconds("1:99:00"))
    }
}
