package com.kys.videomanager.hlsplaylist

object HlsProbeDebugLog {
    const val TAG = "DDDDD"
    private const val MAX_URL_LENGTH = 120

    fun line(phase: String, url: String?, details: String = ""): String {
        val base = "$phase url=${shorten(url)}"
        return if (details.isBlank()) base else "$base $details"
    }

    fun shorten(url: String?): String {
        if (url.isNullOrBlank()) return "(empty)"
        return if (url.length <= MAX_URL_LENGTH) {
            url
        } else {
            url.take(MAX_URL_LENGTH) + "..."
        }
    }
}
