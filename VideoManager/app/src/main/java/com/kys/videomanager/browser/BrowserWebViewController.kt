package com.kys.videomanager.browser
import com.kys.videomanager.R
import com.kys.videomanager.hls.HlsDownloadRequest
import com.kys.videomanager.hls.HlsDownloadService
import com.kys.videomanager.hlsplaylist.HlsDebugRecorder
import com.kys.videomanager.hlsplaylist.HlsPlaylistScannerScript
import com.kys.videomanager.hlsplaylist.HlsProbeDebugLog
import com.kys.videomanager.hlsplaylist.HlsProbeMatch
import com.kys.videomanager.hlsplaylist.HlsProbeRequest
import com.kys.videomanager.hlsplaylist.HlsProbeResponse
import com.kys.videomanager.hlsplaylist.HlsRequestProbe
import com.kys.videomanager.hlsplaylist.HlsStreamDetector

import android.annotation.SuppressLint
import android.content.Context
import android.os.Build
import android.text.TextUtils
import android.util.Log
import android.view.Gravity
import android.view.View
import android.view.inputmethod.EditorInfo
import android.view.inputmethod.InputMethodManager
import android.webkit.ConsoleMessage
import android.webkit.CookieManager
import android.webkit.JavascriptInterface
import android.webkit.ServiceWorkerClient
import android.webkit.ServiceWorkerController
import android.webkit.WebResourceRequest
import android.webkit.WebResourceResponse
import android.webkit.WebChromeClient
import android.webkit.WebView
import android.webkit.WebViewClient
import android.widget.Button
import android.widget.EditText
import android.widget.LinearLayout
import android.widget.TextView
import android.widget.Toast
import androidx.appcompat.app.AppCompatActivity
import androidx.core.content.ContextCompat
import com.google.android.material.bottomsheet.BottomSheetDialog
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
 * 범용 인앱 브라우저. 특정 도메인을 홈으로 두지 않고, 사용자가 입력한 임의의 주소를 방문한다.
 * 즐겨찾기/마지막 접속 주소는 BrowserPreferenceManager에 저장하고,
 * 방문 중인 페이지에서 감지된 HLS 스트림은 HlsDownloadService로 다운로드한다.
 */
class BrowserWebViewController(
    private val activity: AppCompatActivity,
    private val root: View,
    private val onOpenDownloads: () -> Unit
) {

    private lateinit var webView: WebView
    private lateinit var editUrl: EditText
    private lateinit var btnGo: Button
    private lateinit var btnFavoriteToggle: Button
    private lateinit var btnFavorites: Button
    private lateinit var btnDownload: Button
    private val scope = CoroutineScope(Dispatchers.Main + SupervisorJob())
    private val debugRecorder = HlsDebugRecorder()
    private val probingUrls = ConcurrentHashMap.newKeySet<String>()
    private var detectedPlaylistUrl: String? = null
    private var detectedDownloadRequest: HlsDownloadRequest? = null
    @Volatile private var clientSideHistoryDepth: Int = 0
    @Volatile private var lastPageUrl: String? = null

    @SuppressLint("SetJavaScriptEnabled")
    fun start() {
        webView = root.findViewById(R.id.web_view)
        editUrl = root.findViewById(R.id.edit_browser_url)
        btnGo = root.findViewById(R.id.btn_browser_go)
        btnFavoriteToggle = root.findViewById(R.id.btn_browser_favorite_toggle)
        btnFavorites = root.findViewById(R.id.btn_browser_favorites)
        btnDownload = root.findViewById(R.id.btn_download_stream)

        webView.webViewClient = object : WebViewClient() {
            override fun shouldInterceptRequest(
                view: WebView,
                request: WebResourceRequest
            ): WebResourceResponse? {
                handleObservedRequest(request)
                return super.shouldInterceptRequest(view, request)
            }

            @Deprecated("Deprecated in Java")
            override fun shouldInterceptRequest(view: WebView, url: String): WebResourceResponse? {
                debugRecorder.record("request", url)
                detectPlaylist(url)
                probeObservedRequest(url, emptyMap())
                return super.shouldInterceptRequest(view, url)
            }

            override fun onPageStarted(view: WebView, url: String, favicon: android.graphics.Bitmap?) {
                lastPageUrl = url
                clientSideHistoryDepth = 0
                detectedPlaylistUrl = null
                detectedDownloadRequest = null
                editUrl.setText(url)
                btnDownload.visibility = View.GONE
                super.onPageStarted(view, url, favicon)
            }

            override fun onPageFinished(view: WebView, url: String) {
                super.onPageFinished(view, url)
                lastPageUrl = url
                editUrl.setText(url)
                updateFavoriteToggle(url)
                BrowserPreferenceManager.saveLastVisited(url, view.title ?: url)
                installClientSideHistoryTracker()
                installPlaylistScanner()
            }
        }
        webView.webChromeClient = object : WebChromeClient() {
            override fun onConsoleMessage(consoleMessage: ConsoleMessage): Boolean {
                debugRecorder.record("console", consoleMessage.message())
                detectPlaylist(consoleMessage.message())
                return super.onConsoleMessage(consoleMessage)
            }
        }
        WebView.setWebContentsDebuggingEnabled(true)
        webView.settings.javaScriptEnabled = true
        webView.settings.domStorageEnabled = true
        webView.settings.mediaPlaybackRequiresUserGesture = false
        webView.settings.setSupportZoom(true)
        webView.settings.builtInZoomControls = true
        webView.settings.displayZoomControls = false
        webView.addJavascriptInterface(HlsJavascriptBridge(), "VideoManagerHls")
        installServiceWorkerRequestProbe()

        val lastUrl = BrowserPreferenceManager.getLastVisitedUrl()
        if (lastUrl != null) {
            editUrl.setText(lastUrl)
            webView.loadUrl(lastUrl)
        }

        btnGo.setOnClickListener { navigateToTypedUrl() }
        editUrl.setOnEditorActionListener { _, actionId, _ ->
            if (actionId == EditorInfo.IME_ACTION_GO || actionId == EditorInfo.IME_ACTION_DONE) {
                navigateToTypedUrl()
                true
            } else {
                false
            }
        }
        btnFavoriteToggle.setOnClickListener { toggleFavoriteForCurrentPage() }
        btnFavorites.setOnClickListener { showFavoritesSheet() }
        btnDownload.setOnClickListener { showDetectedPlaylist() }

        updateFavoriteToggle(lastUrl)
    }

    fun destroy() {
        if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.N) {
            ServiceWorkerController.getInstance().setServiceWorkerClient(null)
        }
        scope.cancel()
        if (::webView.isInitialized) {
            webView.destroy()
        }
    }

    fun canGoBack(): Boolean =
        ::webView.isInitialized && (webView.canGoBack() || clientSideHistoryDepth > 0)

    fun goBack() {
        when {
            clientSideHistoryDepth > 0 -> {
                clientSideHistoryDepth = (clientSideHistoryDepth - 1).coerceAtLeast(0)
                webView.evaluateJavascript("history.back();", null)
            }
            webView.canGoBack() -> webView.goBack()
        }
    }

    fun handleBack(): Boolean {
        if (!canGoBack()) return false
        goBack()
        return true
    }

    // --- 주소 입력 -------------------------------------------------------------

    private fun navigateToTypedUrl() {
        val normalized = BrowserUrlNormalizer.normalize(editUrl.text.toString())
        if (normalized == null) {
            Toast.makeText(activity, "주소를 입력해 주세요.", Toast.LENGTH_SHORT).show()
            return
        }
        hideKeyboard()
        webView.loadUrl(normalized)
    }

    private fun hideKeyboard() {
        val imm = activity.getSystemService(Context.INPUT_METHOD_SERVICE) as? InputMethodManager
        imm?.hideSoftInputFromWindow(editUrl.windowToken, 0)
    }

    // --- 즐겨찾기 ---------------------------------------------------------------

    private fun updateFavoriteToggle(url: String?) {
        val isFavorite = url != null && BrowserPreferenceManager.isFavorite(url)
        btnFavoriteToggle.text = if (isFavorite) "★" else "☆"
    }

    private fun toggleFavoriteForCurrentPage() {
        val url = webView.url ?: run {
            Toast.makeText(activity, "즐겨찾기에 추가할 페이지가 없습니다.", Toast.LENGTH_SHORT).show()
            return
        }
        if (BrowserPreferenceManager.isFavorite(url)) {
            BrowserPreferenceManager.removeFavorite(url)
            Toast.makeText(activity, "즐겨찾기에서 제거했습니다.", Toast.LENGTH_SHORT).show()
        } else {
            BrowserPreferenceManager.addFavorite(BrowserFavorite(url = url, title = webView.title ?: url))
            Toast.makeText(activity, "즐겨찾기에 추가했습니다.", Toast.LENGTH_SHORT).show()
        }
        updateFavoriteToggle(url)
    }

    private fun showFavoritesSheet() {
        val dialog = BottomSheetDialog(activity, R.style.ThemeOverlay_VideoManager_BottomSheet)
        val container = LinearLayout(activity).apply {
            orientation = LinearLayout.VERTICAL
            setPadding(dp(8), dp(12), dp(8), dp(12))
        }

        fun render() {
            container.removeAllViews()
            container.addView(TextView(activity).apply {
                text = "즐겨찾기"
                setTextColor(ContextCompat.getColor(activity, R.color.text_secondary))
                textSize = 13f
                setPadding(dp(10), 0, dp(10), dp(10))
            })
            val favorites = BrowserPreferenceManager.getFavorites()
            if (favorites.isEmpty()) {
                container.addView(TextView(activity).apply {
                    text = "저장된 즐겨찾기가 없습니다."
                    setTextColor(ContextCompat.getColor(activity, R.color.text_muted))
                    textSize = 14f
                    setPadding(dp(10), dp(4), dp(10), dp(10))
                })
                return
            }
            favorites.forEach { favorite ->
                container.addView(createFavoriteRow(favorite, onOpen = {
                    webView.loadUrl(favorite.url)
                    dialog.dismiss()
                }, onDelete = {
                    BrowserPreferenceManager.removeFavorite(favorite.url)
                    updateFavoriteToggle(webView.url)
                    render()
                }))
            }
        }

        render()
        dialog.setContentView(container)
        dialog.show()
    }

    private fun createFavoriteRow(
        favorite: BrowserFavorite,
        onOpen: () -> Unit,
        onDelete: () -> Unit
    ): View {
        val row = LinearLayout(activity).apply {
            orientation = LinearLayout.HORIZONTAL
            gravity = Gravity.CENTER_VERTICAL
            minimumHeight = dp(50)
            setPadding(dp(10), dp(4), dp(10), dp(4))
            background = ContextCompat.getDrawable(activity, R.drawable.bg_dialog_list_selector)
            isClickable = true
            isFocusable = true
            setOnClickListener { onOpen() }
        }
        val textColumn = LinearLayout(activity).apply {
            orientation = LinearLayout.VERTICAL
            layoutParams = LinearLayout.LayoutParams(0, LinearLayout.LayoutParams.WRAP_CONTENT, 1f)
        }
        textColumn.addView(TextView(activity).apply {
            text = favorite.title
            textSize = 15f
            maxLines = 1
            ellipsize = TextUtils.TruncateAt.END
            setTextColor(ContextCompat.getColor(activity, R.color.text_primary))
        })
        textColumn.addView(TextView(activity).apply {
            text = favorite.url
            textSize = 12f
            maxLines = 1
            ellipsize = TextUtils.TruncateAt.END
            setTextColor(ContextCompat.getColor(activity, R.color.text_muted))
        })
        row.addView(textColumn)
        row.addView(TextView(activity).apply {
            text = "삭제"
            textSize = 13f
            setTextColor(ContextCompat.getColor(activity, R.color.danger))
            setPadding(dp(10), dp(6), dp(6), dp(6))
            isClickable = true
            isFocusable = true
            setOnClickListener { onDelete() }
        })
        return row
    }

    private fun dp(value: Int): Int =
        (value * activity.resources.displayMetrics.density).toInt()

    // --- HLS 스트림 감지 ---------------------------------------------------------

    private fun handleObservedRequest(request: WebResourceRequest?) {
        val requestUrl = request?.url?.toString() ?: return
        debugRecorder.record("request", requestUrl)
        detectPlaylist(requestUrl)
        probeObservedRequest(requestUrl, request.requestHeaders.orEmpty())
    }

    private fun probeObservedRequest(requestUrl: String, requestHeaders: Map<String, String>) {
        if (!HlsRequestProbe.shouldInspectRequest(requestUrl)) return
        if (!probingUrls.add(requestUrl)) return

        scope.launch {
            try {
                val pageUrl = lastPageUrl ?: webView.url
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
                    debugRecorder.record("probe-${match.reason}", match.playlistUrl)
                    showPlaylist(
                        playlistUrl = match.playlistUrl,
                        pageUrl = pageUrl,
                        requestHeaders = requestHeaders,
                        cookie = cookie
                    )
                }
            } finally {
                probingUrls.remove(requestUrl)
            }
        }
    }

    private fun fetchProbeMatch(request: HlsProbeRequest): HlsProbeMatch? {
        val connection = try {
            (URL(request.url).openConnection() as HttpURLConnection).apply {
                connectTimeout = PROBE_CONNECT_TIMEOUT_MS
                readTimeout = PROBE_READ_TIMEOUT_MS
                instanceFollowRedirects = true
                HlsRequestProbe.buildHeaders(request).forEach { (name, value) ->
                    setRequestProperty(name, value)
                }
            }
        } catch (e: Exception) {
            debugRecorder.record("probe-open-failed", "${request.url} (${e.javaClass.simpleName})")
            return null
        }

        return try {
            val code = connection.responseCode
            val contentType = connection.contentType
            if (code !in 200..399) {
                debugRecorder.record("probe-http-$code", request.url)
                return null
            }

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
            debugRecorder.record("probe-read-failed", "${request.url} (${e.javaClass.simpleName})")
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

    private fun installServiceWorkerRequestProbe() {
        if (Build.VERSION.SDK_INT < Build.VERSION_CODES.N) return
        ServiceWorkerController.getInstance().setServiceWorkerClient(
            object : ServiceWorkerClient() {
                override fun shouldInterceptRequest(request: WebResourceRequest): WebResourceResponse? {
                    handleObservedRequest(request)
                    return null
                }
            }
        )
    }

    private fun detectPlaylist(url: String) {
        val playlistUrl = if (HlsStreamDetector.isPlaylistUrl(url)) {
            url
        } else {
            HlsStreamDetector.extractPlaylistUrl(url)
        } ?: return

        showPlaylist(playlistUrl = playlistUrl)
    }

    private fun showPlaylist(
        playlistUrl: String,
        pageUrl: String? = lastPageUrl,
        requestHeaders: Map<String, String> = emptyMap(),
        cookie: String? = null
    ) {
        detectedPlaylistUrl = playlistUrl
        detectedDownloadRequest = HlsDownloadRequest(
            id = "hls-${System.currentTimeMillis()}-${(0..9999).random()}",
            playlistUrl = playlistUrl,
            pageUrl = pageUrl,
            requestHeaders = requestHeaders,
            cookie = cookie,
            title = buildDownloadTitle()
        )
        Log.d(HlsProbeDebugLog.TAG, HlsProbeDebugLog.line("playlist-detected", playlistUrl))
        activity.runOnUiThread {
            btnDownload.visibility = View.VISIBLE
            Toast.makeText(activity, "m3u8 스트림을 감지했습니다.", Toast.LENGTH_SHORT).show()
        }
    }

    private fun installPlaylistScanner() {
        webView.evaluateJavascript(HlsPlaylistScannerScript.JS, null)
    }

    private fun installClientSideHistoryTracker() {
        webView.evaluateJavascript(
            """
            (function() {
              if (window.__videoManagerHistoryTrackerInstalled) {
                try {
                  window.VideoManagerHls.onClientHistoryChanged(
                    window.__videoManagerClientHistoryDepth || 0,
                    location.href
                  );
                } catch (e) {}
                return;
              }
              window.__videoManagerHistoryTrackerInstalled = true;
              window.__videoManagerClientHistoryDepth = 0;
              function notifyHistoryChanged() {
                try {
                  window.VideoManagerHls.onClientHistoryChanged(
                    window.__videoManagerClientHistoryDepth || 0,
                    location.href
                  );
                } catch (e) {}
              }
              var originalPushState = history.pushState;
              history.pushState = function() {
                var result = originalPushState.apply(this, arguments);
                window.__videoManagerClientHistoryDepth =
                  (window.__videoManagerClientHistoryDepth || 0) + 1;
                notifyHistoryChanged();
                return result;
              };
              var originalReplaceState = history.replaceState;
              history.replaceState = function() {
                var result = originalReplaceState.apply(this, arguments);
                notifyHistoryChanged();
                return result;
              };
              window.addEventListener('popstate', function() {
                window.__videoManagerClientHistoryDepth = Math.max(
                  0,
                  (window.__videoManagerClientHistoryDepth || 0) - 1
                );
                notifyHistoryChanged();
              });
              notifyHistoryChanged();
            })();
            """.trimIndent(),
            null
        )
    }

    private inner class HlsJavascriptBridge {
        @JavascriptInterface
        fun onPlaylistFound(url: String) {
            detectPlaylist(url)
        }

        @JavascriptInterface
        fun onNetworkSeen(value: String) {
            debugRecorder.record("web", value)
            detectPlaylist(value)
        }

        @JavascriptInterface
        fun onClientHistoryChanged(depth: Int, url: String?) {
            clientSideHistoryDepth = depth.coerceAtLeast(0)
            lastPageUrl = url ?: lastPageUrl
        }
    }

    private fun showDetectedPlaylist() {
        val request = detectedDownloadRequest
        if (request == null || detectedPlaylistUrl == null) {
            Toast.makeText(activity, "감지된 m3u8 스트림이 없습니다.", Toast.LENGTH_SHORT).show()
            return
        }

        HlsDownloadService.start(activity, request)
        onOpenDownloads()
        Toast.makeText(activity, "다운로드를 시작했습니다.", Toast.LENGTH_SHORT).show()
    }

    private fun buildDownloadTitle(): String {
        val source = lastPageUrl ?: detectedPlaylistUrl.orEmpty()
        return source
            .trimEnd('/')
            .substringAfterLast('/')
            .substringBefore('?')
            .ifBlank { "hls_${System.currentTimeMillis()}" }
    }

    companion object {
        private const val MAX_PROBE_BODY_CHARS = 256_000
        private const val PROBE_CONNECT_TIMEOUT_MS = 8_000
        private const val PROBE_READ_TIMEOUT_MS = 8_000
    }
}
