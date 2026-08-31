package com.kys.videomanager.hlsplaylist

import android.util.Log
import android.webkit.CookieManager
import android.webkit.JavascriptInterface
import android.webkit.WebResourceRequest
import android.webkit.WebResourceResponse
import android.webkit.WebView
import android.webkit.WebViewClient
import kotlinx.coroutines.CoroutineScope
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.SupervisorJob
import kotlinx.coroutines.cancel
import kotlinx.coroutines.launch
import kotlinx.coroutines.withContext
import java.net.HttpURLConnection
import java.net.URL
import java.util.concurrent.ConcurrentHashMap

/**
 * Attaches HLS-playlist detection (network interception + JS scanner) to any [WebView] —
 * the visible browsing tab or a headless instance used for token refresh. Reports only the
 * first match found; callers own the WebView's lifecycle.
 */
class HlsPlaylistProbeSession(
    private val webView: WebView,
    private val onFound: (playlistUrl: String, requestHeaders: Map<String, String>, cookie: String?) -> Unit
) {
    private val scope = CoroutineScope(Dispatchers.Main + SupervisorJob())
    private val probingUrls = ConcurrentHashMap.newKeySet<String>()
    @Volatile private var found = false
    @Volatile private var pageUrl: String? = null

    fun attachAndLoad(pageUrl: String) {
        this.pageUrl = pageUrl
        webView.webViewClient = object : WebViewClient() {
            override fun shouldInterceptRequest(
                view: WebView,
                request: WebResourceRequest
            ): WebResourceResponse? {
                handleObservedRequest(request)
                return super.shouldInterceptRequest(view, request)
            }

            override fun onPageFinished(view: WebView, url: String) {
                super.onPageFinished(view, url)
                webView.evaluateJavascript(HlsPlaylistScannerScript.JS, null)
            }
        }
        webView.addJavascriptInterface(JsBridge(), "VideoManagerHls")
        webView.settings.javaScriptEnabled = true
        webView.settings.domStorageEnabled = true
        webView.loadUrl(pageUrl)
    }

    fun close() {
        scope.cancel()
    }

    private fun handleObservedRequest(request: WebResourceRequest) {
        if (found) return
        val requestUrl = request.url?.toString() ?: return
        probeObservedRequest(requestUrl, request.requestHeaders.orEmpty())
    }

    private fun probeObservedRequest(requestUrl: String, requestHeaders: Map<String, String>) {
        if (found) return
        if (!HlsRequestProbe.shouldInspectRequest(requestUrl)) return
        if (!probingUrls.add(requestUrl)) return

        scope.launch {
            try {
                if (found) return@launch
                val cookie = CookieManager.getInstance().getCookie(requestUrl)
                val match = withContext(Dispatchers.IO) {
                    fetchProbeMatch(
                        HlsProbeRequest(
                            url = requestUrl,
                            pageUrl = pageUrl,
                            requestHeaders = requestHeaders,
                            cookie = cookie
                        )
                    )
                }
                if (match != null) {
                    report(match.playlistUrl, requestHeaders, cookie)
                }
            } finally {
                probingUrls.remove(requestUrl)
            }
        }
    }

    private fun report(playlistUrl: String, requestHeaders: Map<String, String>, cookie: String?) {
        if (found) return
        found = true
        onFound(playlistUrl, requestHeaders, cookie)
    }

    private fun fetchProbeMatch(request: HlsProbeRequest): HlsProbeMatch? {
        val connection = try {
            (URL(request.url).openConnection() as HttpURLConnection).apply {
                connectTimeout = CONNECT_TIMEOUT_MS
                readTimeout = READ_TIMEOUT_MS
                instanceFollowRedirects = true
                HlsRequestProbe.buildHeaders(request).forEach { (name, value) ->
                    setRequestProperty(name, value)
                }
            }
        } catch (e: Exception) {
            Log.d(DEBUG_TAG, "token-refresh-probe-open-failed url=${request.url} error=${e.javaClass.simpleName}")
            return null
        }

        return try {
            val code = connection.responseCode
            val contentType = connection.contentType
            if (code !in 200..399) return null

            val directMatch = HlsRequestProbe.detect(
                HlsProbeResponse(requestUrl = connection.url.toString(), contentType = contentType, body = null)
            )
            if (directMatch != null) return directMatch

            val body = if (HlsRequestProbe.shouldReadBody(contentType)) {
                connection.inputStream.use { input -> input.reader().readTextLimited(MAX_PROBE_BODY_CHARS) }
            } else {
                null
            }
            HlsRequestProbe.detect(
                HlsProbeResponse(requestUrl = connection.url.toString(), contentType = contentType, body = body)
            )
        } catch (e: Exception) {
            Log.d(DEBUG_TAG, "token-refresh-probe-read-failed url=${request.url} error=${e.javaClass.simpleName}")
            null
        } finally {
            connection.disconnect()
        }
    }

    private fun java.io.Reader.readTextLimited(maxChars: Int): String {
        val buffer = CharArray(4096)
        val builder = StringBuilder()
        while (builder.length < maxChars) {
            val read = read(buffer, 0, minOf(buffer.size, maxChars - builder.length))
            if (read == -1) break
            builder.append(buffer, 0, read)
        }
        return builder.toString()
    }

    private inner class JsBridge {
        @JavascriptInterface
        fun onPlaylistFound(url: String) = onScannerHit(url)

        @JavascriptInterface
        fun onNetworkSeen(value: String) = onScannerHit(value)

        private fun onScannerHit(value: String) {
            if (found) return
            val playlistUrl = if (HlsStreamDetector.isPlaylistUrl(value)) {
                value
            } else {
                HlsStreamDetector.extractPlaylistUrl(value)
            } ?: return
            val cookie = CookieManager.getInstance().getCookie(playlistUrl)
            report(playlistUrl, emptyMap(), cookie)
        }
    }

    companion object {
        private const val DEBUG_TAG = "DDDDD"
        private const val MAX_PROBE_BODY_CHARS = 256_000
        private const val CONNECT_TIMEOUT_MS = 8_000
        private const val READ_TIMEOUT_MS = 8_000
    }
}
