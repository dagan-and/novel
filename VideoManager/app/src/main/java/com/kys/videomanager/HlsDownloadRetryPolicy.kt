package com.kys.videomanager

import java.io.IOException

enum class HlsDownloadFailureKind {
    TRANSIENT,
    NOT_RETRYABLE,
    UNSUPPORTED
}

enum class HlsDownloadStage {
    PLAYLIST,
    SEGMENT
}

class HlsDownloadException(
    message: String,
    val kind: HlsDownloadFailureKind,
    val retryAfterMillis: Long? = null,
    val stage: HlsDownloadStage = HlsDownloadStage.SEGMENT,
    val httpCode: Int? = null,
    cause: Throwable? = null
) : Exception(message, cause)

data class HlsDownloadRetryDecision(
    val shouldRetry: Boolean,
    val delayMillis: Long
)

object HlsDownloadRetryPolicy {
    const val maxRetries = 3
    private val RETRY_DELAYS_MS = listOf(60_000L, 300_000L, 900_000L)

    fun retryDecision(error: Throwable, completedAttempts: Int): HlsDownloadRetryDecision {
        if (completedAttempts >= maxRetries || !error.isRetryable()) {
            return HlsDownloadRetryDecision(shouldRetry = false, delayMillis = 0L)
        }
        val defaultDelay = RETRY_DELAYS_MS.getOrElse(completedAttempts) { RETRY_DELAYS_MS.last() }
        val retryAfterDelay = (error as? HlsDownloadException)?.retryAfterMillis
        return HlsDownloadRetryDecision(
            shouldRetry = true,
            delayMillis = retryAfterDelay?.coerceAtLeast(defaultDelay) ?: defaultDelay
        )
    }

    private fun Throwable.isRetryable(): Boolean =
        when (this) {
            is HlsDownloadException -> kind == HlsDownloadFailureKind.TRANSIENT
            is IOException -> true
            else -> false
        }
}
