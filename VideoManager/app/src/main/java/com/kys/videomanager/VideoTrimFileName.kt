package com.kys.videomanager

object VideoTrimFileName {
    fun defaultEditableName(originalName: String): String =
        originalName.substringBeforeLast('.', originalName).ifBlank { originalName }

    fun outputName(originalName: String, requestedName: String): String {
        val cleanRequested = requestedName.trim().ifBlank { defaultEditableName(originalName) }
        val fallbackBase = VideoFileNameSanitizer.sanitizeBaseName(defaultEditableName(originalName))
        val explicitExtension = cleanRequested.substringAfterLast('.', "")
        val baseName = if (explicitExtension.isNotBlank()) {
            cleanRequested.substringBeforeLast('.', cleanRequested)
        } else {
            cleanRequested
        }
        val extension = if (explicitExtension.isNotBlank()) {
            VideoFileNameSanitizer.sanitizeExtension(explicitExtension)
        } else {
            VideoFileNameSanitizer.sanitizeExtension(originalName.substringAfterLast('.', "mp4"))
        }
        return "${VideoFileNameSanitizer.sanitizeBaseName(baseName, fallbackBase)}.$extension"
    }
}
