package com.kys.videomanager.hlsplaylist

import java.net.URI

data class HlsPageAnalysis(
    val playlistUrl: String?,
    val followUrls: List<String>
)

object HlsPageAnalyzer {
    private val mediaPagePattern = Regex(
        """<(iframe|script|source|video)\b[^>]*(src|href)=["']([^"']+)["']""",
        setOf(RegexOption.IGNORE_CASE, RegexOption.MULTILINE)
    )

    fun analyze(pageUrl: String, html: String): HlsPageAnalysis {
        val playlistUrl = HlsStreamDetector.extractPlaylistUrl(html)
        if (playlistUrl != null) {
            return HlsPageAnalysis(playlistUrl = playlistUrl, followUrls = emptyList())
        }

        val followUrls = mediaPagePattern.findAll(html)
            .mapNotNull { match -> resolveUrl(pageUrl, match.groupValues[3]) }
            .distinct()
            .toList()

        return HlsPageAnalysis(playlistUrl = null, followUrls = followUrls)
    }

    private fun resolveUrl(pageUrl: String, candidate: String): String? {
        if (candidate.isBlank() || candidate.startsWith("data:", ignoreCase = true)) return null

        return try {
            URI(pageUrl).resolve(candidate).toString()
        } catch (_: IllegalArgumentException) {
            null
        }
    }
}
