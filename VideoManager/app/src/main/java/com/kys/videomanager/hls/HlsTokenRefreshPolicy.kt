package com.kys.videomanager.hls

object HlsTokenRefreshPolicy {
    const val maxAttempts = 2
    private val TOKEN_BLOCKED_CODES = setOf(401, 403, 410)

    fun isTokenBlockedFailure(error: Throwable): Boolean {
        val exception = error as? HlsDownloadException ?: return false
        if (exception.stage != HlsDownloadStage.PLAYLIST) return false
        return exception.httpCode in TOKEN_BLOCKED_CODES
    }

    fun shouldAttemptRefresh(error: Throwable, completedRefreshAttempts: Int): Boolean =
        completedRefreshAttempts < maxAttempts && isTokenBlockedFailure(error)
}
