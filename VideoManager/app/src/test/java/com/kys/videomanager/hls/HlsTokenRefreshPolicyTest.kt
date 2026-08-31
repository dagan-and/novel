package com.kys.videomanager.hls

import org.junit.Assert.assertFalse
import org.junit.Assert.assertTrue
import org.junit.Test
import java.io.IOException

class HlsTokenRefreshPolicyTest {

    @Test
    fun `playlist auth failure attempts refresh`() {
        val error = HlsDownloadException(
            "HTTP 403",
            HlsDownloadFailureKind.NOT_RETRYABLE,
            stage = HlsDownloadStage.PLAYLIST,
            httpCode = 403
        )

        assertTrue(HlsTokenRefreshPolicy.shouldAttemptRefresh(error, completedRefreshAttempts = 0))
    }

    @Test
    fun `playlist not found does not attempt refresh`() {
        val error = HlsDownloadException(
            "HTTP 404",
            HlsDownloadFailureKind.NOT_RETRYABLE,
            stage = HlsDownloadStage.PLAYLIST,
            httpCode = 404
        )

        assertFalse(HlsTokenRefreshPolicy.shouldAttemptRefresh(error, completedRefreshAttempts = 0))
    }

    @Test
    fun `segment stage failure does not attempt refresh`() {
        val error = HlsDownloadException(
            "segment HTTP 403",
            HlsDownloadFailureKind.NOT_RETRYABLE,
            stage = HlsDownloadStage.SEGMENT,
            httpCode = 403
        )

        assertFalse(HlsTokenRefreshPolicy.shouldAttemptRefresh(error, completedRefreshAttempts = 0))
    }

    @Test
    fun `stops after max refresh attempts`() {
        val error = HlsDownloadException(
            "HTTP 401",
            HlsDownloadFailureKind.NOT_RETRYABLE,
            stage = HlsDownloadStage.PLAYLIST,
            httpCode = 401
        )

        assertFalse(
            HlsTokenRefreshPolicy.shouldAttemptRefresh(
                error,
                completedRefreshAttempts = HlsTokenRefreshPolicy.maxAttempts
            )
        )
    }

    @Test
    fun `non http exceptions do not attempt refresh`() {
        assertFalse(HlsTokenRefreshPolicy.shouldAttemptRefresh(IOException("network drop"), completedRefreshAttempts = 0))
    }
}
