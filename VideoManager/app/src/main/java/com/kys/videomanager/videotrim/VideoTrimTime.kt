package com.kys.videomanager.videotrim

object VideoTrimTime {
    fun parseSeconds(input: String): Long? {
        val trimmed = input.trim()
        if (trimmed.isEmpty()) return null
        if (trimmed.all { it.isDigit() }) return parseCompactSeconds(trimmed)

        val parts = trimmed.split(":")
        if (parts.size !in 1..3) return null
        val values = parts.map { it.toLongOrNull() ?: return null }
        if (values.any { it < 0L }) return null
        val hours: Long
        val minutes: Long
        val seconds: Long
        when (values.size) {
            1 -> {
                hours = 0L
                minutes = 0L
                seconds = values[0]
            }
            2 -> {
                hours = 0L
                minutes = values[0]
                seconds = values[1]
            }
            else -> {
                hours = values[0]
                minutes = values[1]
                seconds = values[2]
            }
        }
        if (minutes >= 60L || seconds >= 60L) return null
        return (hours * 3600L) + (minutes * 60L) + seconds
    }

    private fun parseCompactSeconds(digits: String): Long? {
        if (digits.length > 6) return null
        val padded = digits.padStart(6, '0')
        val hours = padded.substring(0, 2).toLong()
        val minutes = padded.substring(2, 4).toLong()
        val seconds = padded.substring(4, 6).toLong()
        if (minutes >= 60L || seconds >= 60L) return null
        return (hours * 3600L) + (minutes * 60L) + seconds
    }

    fun formatTimestamp(totalSeconds: Long): String {
        val bounded = totalSeconds.coerceAtLeast(0L)
        val hours = bounded / 3600L
        val minutes = (bounded % 3600L) / 60L
        val seconds = bounded % 60L
        return "%02d:%02d:%02d".format(hours, minutes, seconds)
    }
}
