package com.kys.videomanager.browser

object BrowserUrlNormalizer {
    private val schemeRegex = Regex("^[a-zA-Z][a-zA-Z0-9+.-]*://")

    fun normalize(input: String): String? {
        val trimmed = input.trim()
        if (trimmed.isBlank()) return null
        return if (schemeRegex.containsMatchIn(trimmed)) trimmed else "https://$trimmed"
    }
}
