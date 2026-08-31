package com.kys.videomanager.hlsplaylist

import org.junit.Assert.assertFalse
import org.junit.Assert.assertTrue
import org.junit.Test

class HlsDebugRecorderTest {

    @Test fun `snapshot includes recent labeled events`() {
        val recorder = HlsDebugRecorder(maxEvents = 3)

        recorder.record("request", "https://upload18.org/play/index/nhdtc-242")
        recorder.record("xhr", "https://upload18.org/api/player")

        val snapshot = recorder.snapshot()

        assertTrue(snapshot.contains("request: https://upload18.org/play/index/nhdtc-242"))
        assertTrue(snapshot.contains("xhr: https://upload18.org/api/player"))
    }

    @Test fun `oldest events are dropped when max is exceeded`() {
        val recorder = HlsDebugRecorder(maxEvents = 2)

        recorder.record("one", "first")
        recorder.record("two", "second")
        recorder.record("three", "third")

        val snapshot = recorder.snapshot()

        assertFalse(snapshot.contains("one: first"))
        assertTrue(snapshot.contains("two: second"))
        assertTrue(snapshot.contains("three: third"))
    }
}
