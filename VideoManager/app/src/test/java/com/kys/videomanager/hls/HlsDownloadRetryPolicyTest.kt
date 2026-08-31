package com.kys.videomanager.hls

import org.junit.Assert.assertEquals
import org.junit.Assert.assertFalse
import org.junit.Assert.assertTrue
import org.junit.Test
import java.io.IOException

class HlsDownloadRetryPolicyTest {
    @Test
    fun `transient network failures retry with slow backoff`() {
        val first = HlsDownloadRetryPolicy.retryDecision(IOException("timeout"), completedAttempts = 0)
        val second = HlsDownloadRetryPolicy.retryDecision(IOException("timeout"), completedAttempts = 1)

        assertTrue(first.shouldRetry)
        assertEquals(60_000L, first.delayMillis)
        assertTrue(second.shouldRetry)
        assertEquals(300_000L, second.delayMillis)
    }

    @Test
    fun `rate limited HTTP failure can retry using retry after`() {
        val decision = HlsDownloadRetryPolicy.retryDecision(
            HlsDownloadException("segment HTTP 429", HlsDownloadFailureKind.TRANSIENT, retryAfterMillis = 120_000L),
            completedAttempts = 0
        )

        assertTrue(decision.shouldRetry)
        assertEquals(120_000L, decision.delayMillis)
    }

    @Test
    fun `authorization and unsupported failures do not retry`() {
        assertFalse(
            HlsDownloadRetryPolicy.retryDecision(
                HlsDownloadException("HTTP 403", HlsDownloadFailureKind.NOT_RETRYABLE),
                completedAttempts = 0
            ).shouldRetry
        )
        assertFalse(
            HlsDownloadRetryPolicy.retryDecision(
                HlsDownloadException("암호화된 HLS는 지원하지 않습니다.", HlsDownloadFailureKind.UNSUPPORTED),
                completedAttempts = 0
            ).shouldRetry
        )
    }

    @Test
    fun `retry stops after configured attempts`() {
        val decision = HlsDownloadRetryPolicy.retryDecision(
            IOException("timeout"),
            completedAttempts = HlsDownloadRetryPolicy.maxRetries
        )

        assertFalse(decision.shouldRetry)
    }
}
