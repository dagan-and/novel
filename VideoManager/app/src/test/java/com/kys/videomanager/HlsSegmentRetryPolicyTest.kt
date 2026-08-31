package com.kys.videomanager

import org.junit.Assert.assertEquals
import org.junit.Assert.assertFalse
import org.junit.Assert.assertTrue
import org.junit.Test

class HlsSegmentRetryPolicyTest {
    @Test
    fun `429 segments are retried using retry after seconds`() {
        val decision = HlsSegmentRetryPolicy.retryDecision(
            responseCode = 429,
            retryAfterHeader = "3",
            attempt = 1
        )

        assertTrue(decision.shouldRetry)
        assertEquals(3_000L, decision.delayMillis)
    }

    @Test
    fun `429 segments without retry after use capped backoff`() {
        val decision = HlsSegmentRetryPolicy.retryDecision(
            responseCode = 429,
            retryAfterHeader = null,
            attempt = 3
        )

        assertTrue(decision.shouldRetry)
        assertEquals(4_000L, decision.delayMillis)
    }

    @Test
    fun `successful and exhausted responses are not retried`() {
        assertFalse(
            HlsSegmentRetryPolicy.retryDecision(
                responseCode = 200,
                retryAfterHeader = null,
                attempt = 1
            ).shouldRetry
        )
        assertFalse(
            HlsSegmentRetryPolicy.retryDecision(
                responseCode = 429,
                retryAfterHeader = "1",
                attempt = HlsSegmentRetryPolicy.maxAttempts
            ).shouldRetry
        )
    }
}
