package com.kys.videomanager

data class HlsSegmentRetryDecision(
    val shouldRetry: Boolean,
    val delayMillis: Long
)

object HlsSegmentRetryPolicy {
    const val maxAttempts = 5
    private const val MAX_DELAY_MS = 30_000L

    fun retryDecision(responseCode: Int, retryAfterHeader: String?, attempt: Int): HlsSegmentRetryDecision {
        if (responseCode !in RETRYABLE_CODES || attempt >= maxAttempts) {
            return HlsSegmentRetryDecision(shouldRetry = false, delayMillis = 0L)
        }
        val retryAfterDelay = retryAfterHeader
            ?.trim()
            ?.toLongOrNull()
            ?.coerceAtLeast(0L)
            ?.times(1_000L)
        val fallbackDelay = (1_000L shl (attempt - 1).coerceAtLeast(0)).coerceAtMost(MAX_DELAY_MS)
        return HlsSegmentRetryDecision(
            shouldRetry = true,
            delayMillis = (retryAfterDelay ?: fallbackDelay).coerceAtMost(MAX_DELAY_MS)
        )
    }

    private val RETRYABLE_CODES = setOf(408, 425, 429, 500, 502, 503, 504)
}
