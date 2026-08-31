package com.kys.videomanager

import org.junit.Assert.assertFalse
import org.junit.Assert.assertTrue
import org.junit.Test

class HlsPlaylistResumeGuardTest {

    @Test
    fun `same segment count can resume`() {
        assertFalse(HlsPlaylistResumeGuard.shouldRestartFromScratch(previousTotalSegments = 1343, newTotalSegments = 1343))
    }

    @Test
    fun `different segment count must restart`() {
        assertTrue(HlsPlaylistResumeGuard.shouldRestartFromScratch(previousTotalSegments = 1343, newTotalSegments = 900))
    }

    @Test
    fun `no previous progress can resume`() {
        assertFalse(HlsPlaylistResumeGuard.shouldRestartFromScratch(previousTotalSegments = 0, newTotalSegments = 1343))
    }
}
