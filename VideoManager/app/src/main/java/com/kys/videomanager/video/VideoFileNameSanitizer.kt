package com.kys.videomanager.video

object VideoFileNameSanitizer {
    private val unsafeCharacters = Regex("""[\\/:*?"<>|\r\n\t]+""")
    private val repeatedWhitespace = Regex("""\s+""")

    fun sanitizeBaseName(value: String, fallback: String = "video"): String {
        val sanitized = value
            .replace(unsafeCharacters, " ")
            .replace(repeatedWhitespace, " ")
            .trim()
            .trim('.')
            .trim()
        return sanitized.ifBlank { fallback }
    }

    fun sanitizeExtension(value: String, fallback: String = "mp4"): String {
        val sanitized = value
            .lowercase()
            .filter { it.isLetterOrDigit() }
            .ifBlank { fallback }
        return sanitized.ifBlank { "mp4" }
    }
}
