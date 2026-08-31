package com.kys.videomanager

import java.net.URI
import java.util.Locale

data class HlsProbeRequest(
    val url: String,
    val pageUrl: String?,
    val requestHeaders: Map<String, String>,
    val cookie: String?
)

data class HlsProbeResponse(
    val requestUrl: String,
    val contentType: String?,
    val body: String?
)

data class HlsProbeMatch(
    val playlistUrl: String,
    val reason: String
)

object HlsRequestProbe {
    private val ignoredExtensions = setOf(
        "css",
        "png",
        "jpg",
        "jpeg",
        "gif",
        "webp",
        "svg",
        "ico",
        "woff",
        "woff2",
        "ttf",
        "otf",
        "map",
        "ts",
        "m4s"
    )
    private val playlistContentTypes = setOf(
        "application/vnd.apple.mpegurl",
        "application/x-mpegurl",
        "audio/mpegurl",
        "audio/x-mpegurl",
        "video/m3u8"
    )

    fun shouldInspectRequest(url: String?): Boolean {
        if (url.isNullOrBlank()) return false
        val uri = try {
            URI(url)
        } catch (_: Exception) {
            return false
        }
        val scheme = uri.scheme?.lowercase(Locale.US)
        if (scheme != "http" && scheme != "https") return false

        val extension = uri.path
            .orEmpty()
            .substringAfterLast('/', "")
            .substringAfterLast('.', "")
            .lowercase(Locale.US)
        return extension !in ignoredExtensions
    }

    fun buildHeaders(request: HlsProbeRequest): Map<String, String> {
        val headers = LinkedHashMap<String, String>()
        request.requestHeaders.forEach { (name, value) ->
            if (name.isNotBlank() && value.isNotBlank()) {
                headers[name] = value
            }
        }
        if (!headers.containsHeader("User-Agent")) {
            headers["User-Agent"] = SearchWebViewController.WEB_USER_AGENT
        }
        if (!headers.containsHeader("Referer") && !request.pageUrl.isNullOrBlank()) {
            headers["Referer"] = request.pageUrl
        }
        if (!headers.containsHeader("Cookie") && !request.cookie.isNullOrBlank()) {
            headers["Cookie"] = request.cookie
        }
        if (!headers.containsHeader("Accept")) {
            headers["Accept"] = "*/*"
        }
        headers.keys.removeAll { it.equals("Accept-Encoding", ignoreCase = true) }
        headers["Accept-Encoding"] = "identity"
        return headers
    }

    fun shouldReadBody(contentType: String?): Boolean {
        if (contentType.isNullOrBlank()) return true
        val lower = contentType.lowercase(Locale.US)
        return lower.startsWith("text/") ||
            lower.contains("json") ||
            lower.contains("javascript") ||
            lower.contains("mpegurl") ||
            lower.contains("m3u8") ||
            lower.contains("xml")
    }

    fun detect(response: HlsProbeResponse): HlsProbeMatch? {
        if (HlsStreamDetector.isPlaylistUrl(response.requestUrl)) {
            return HlsProbeMatch(response.requestUrl, "url")
        }
        if (isPlaylistContentType(response.contentType)) {
            return HlsProbeMatch(response.requestUrl, "content-type")
        }
        val playlistUrl = HlsStreamDetector.extractPlaylistUrl(response.body)
        return playlistUrl?.let { HlsProbeMatch(it, "body") }
    }

    private fun isPlaylistContentType(contentType: String?): Boolean {
        if (contentType.isNullOrBlank()) return false
        val normalized = contentType.substringBefore(';').trim().lowercase(Locale.US)
        return normalized in playlistContentTypes
    }

    private fun Map<String, String>.containsHeader(name: String): Boolean {
        return keys.any { it.equals(name, ignoreCase = true) }
    }
}
