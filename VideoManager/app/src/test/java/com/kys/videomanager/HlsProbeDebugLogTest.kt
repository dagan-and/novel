package com.kys.videomanager

import org.junit.Assert.assertEquals
import org.junit.Assert.assertTrue
import org.junit.Test

class HlsProbeDebugLogTest {

    @Test fun `long url is shortened for readable logcat output`() {
        val longUrl = "https://cdn.example.com/" + "a".repeat(180) + "/master.m3u8"

        val result = HlsProbeDebugLog.shorten(longUrl)

        assertTrue(result.length <= 123)
        assertTrue(result.startsWith("https://cdn.example.com/"))
        assertTrue(result.endsWith("..."))
    }

    @Test fun `request line includes phase and shortened url`() {
        val result = HlsProbeDebugLog.line(
            phase = "probe-start",
            url = "https://upload18.org/play/index/nhdtc-242",
            details = "headers=4 cookie=true"
        )

        assertEquals(
            "probe-start url=https://upload18.org/play/index/nhdtc-242 headers=4 cookie=true",
            result
        )
    }
}
