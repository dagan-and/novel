package com.kys.videomanager.hlsplaylist

object HlsStreamDetector {
    private val playlistPattern = Regex("""https?://[^'"<>\s]+\.m3u8[^'"<>\s]*""", RegexOption.IGNORE_CASE)

    fun isPlaylistUrl(url: String?): Boolean {
        if (url.isNullOrBlank()) return false

        val withoutQuery = url.substringBefore("?")
        return withoutQuery.endsWith(".m3u8", ignoreCase = true)
    }

    fun extractPlaylistUrl(text: String?): String? {
        if (text.isNullOrBlank()) return null

        val normalizedText = text
            .replace("\\/", "/")
            .replace("&amp;", "&")
        return playlistPattern.find(normalizedText)?.value
    }
}
