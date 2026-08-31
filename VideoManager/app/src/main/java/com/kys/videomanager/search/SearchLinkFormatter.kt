package com.kys.videomanager.search

import java.net.URI
import java.net.URLEncoder
import java.util.Locale

object SearchLinkFormatter {
    private const val DETAIL_HOST = "avdbapi.com"
    private const val UPLOAD18_PREFIX = "https://upload18.org/play/index/"
    private const val POSTER_PREFIX = "https://upload18.cc/v/"
    private const val POSTER_SUFFIX = "/poster.jpg"
    private const val GOOGLE_TRANSLATE_PREFIX = "https://translate.google.com/translate?sl=auto&tl=ko&u="

    fun toUpload18Url(currentUrl: String?): String? {
        val code = extractDetailCode(currentUrl) ?: return null
        return UPLOAD18_PREFIX + code
    }

    fun toPosterImageUrl(currentUrl: String?): String? {
        val code = extractDetailCode(currentUrl) ?: return null
        return POSTER_PREFIX + code.uppercase(Locale.ROOT) + POSTER_SUFFIX
    }

    fun toPosterViewerHtml(posterUrl: String): String {
        val escapedPosterUrl = posterUrl
            .replace("&", "&amp;")
            .replace("\"", "&quot;")
            .replace("<", "&lt;")
            .replace(">", "&gt;")

        return """
            <!doctype html>
            <html>
            <head>
              <meta name="viewport" content="width=device-width, initial-scale=1.0, minimum-scale=1.0, maximum-scale=5.0, user-scalable=yes">
              <style>
                html, body {
                  width: 100%;
                  height: 100%;
                  margin: 0;
                  background: #111111;
                }
                body {
                  display:flex;
                  align-items:center;
                  justify-content:center;
                  overflow:auto;
                }
                img {
                  max-width: 100%;
                  height: auto;
                  object-fit: contain;
                }
              </style>
            </head>
            <body>
              <img src="$escapedPosterUrl" alt="poster">
            </body>
            </html>
        """.trimIndent()
    }

    fun toGoogleTranslateUrl(currentUrl: String?): String? {
        if (currentUrl.isNullOrBlank()) return null

        return GOOGLE_TRANSLATE_PREFIX + URLEncoder.encode(currentUrl, "UTF-8")
    }

    private fun extractDetailCode(currentUrl: String?): String? {
        if (currentUrl.isNullOrBlank()) return null

        val uri = try {
            URI(currentUrl)
        } catch (_: IllegalArgumentException) {
            return null
        }
        val host = uri.host?.removePrefix("www.") ?: return null
        val segments = uri.path
            ?.split("/")
            ?.filter { it.isNotBlank() }
            ?: return null
        if (host != DETAIL_HOST || segments.size < 2 || segments[0] != "detail") return null

        return segments[1].takeIf { it.isNotBlank() }
    }
}
