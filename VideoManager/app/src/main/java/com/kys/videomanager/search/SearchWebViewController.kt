package com.kys.videomanager.search
import com.kys.videomanager.R
import com.kys.videomanager.main.MainScreenUiModel
import com.kys.videomanager.downloadstatus.DownloadStatusActivity
import com.kys.videomanager.hls.HlsDownloadRequest
import com.kys.videomanager.hls.HlsDownloadService
import com.kys.videomanager.hlsplaylist.HlsDebugRecorder
import com.kys.videomanager.hlsplaylist.HlsPageAnalyzer
import com.kys.videomanager.hlsplaylist.HlsPlaylistScannerScript
import com.kys.videomanager.hlsplaylist.HlsProbeDebugLog
import com.kys.videomanager.hlsplaylist.HlsProbeMatch
import com.kys.videomanager.hlsplaylist.HlsProbeRequest
import com.kys.videomanager.hlsplaylist.HlsProbeResponse
import com.kys.videomanager.hlsplaylist.HlsRequestProbe
import com.kys.videomanager.hlsplaylist.HlsStreamDetector

import android.annotation.SuppressLint
import android.app.Dialog
import android.content.ClipboardManager
import android.content.Context
import android.content.Intent
import android.graphics.Bitmap
import android.graphics.Color
import android.graphics.drawable.ColorDrawable
import android.net.Uri
import android.os.Build
import android.util.Log
import android.view.Gravity
import android.view.View
import android.view.ViewGroup
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
import android.widget.FrameLayout
import android.widget.ImageView
import android.widget.Toast
import androidx.appcompat.app.AppCompatActivity
import com.bumptech.glide.Glide
import kotlinx.coroutines.CoroutineScope
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.SupervisorJob
import kotlinx.coroutines.cancel
import kotlinx.coroutines.launch
import kotlinx.coroutines.withContext
import java.net.HttpURLConnection
import java.net.URL
import java.util.concurrent.ConcurrentHashMap

class SearchWebViewController(
    private val activity: AppCompatActivity,
    private val root: View,
    private val homeUrl: String = MainScreenUiModel.searchHomeUrl,
    private val onClose: () -> Unit = { activity.finish() },
    private val onOpenDownloads: () -> Unit = {
        activity.startActivity(Intent(activity, DownloadStatusActivity::class.java))
    }
) {

    private lateinit var webView: WebView
    private lateinit var btnCopy: Button
    private lateinit var btnFindStream: Button
    private lateinit var btnPoster: Button
    private var btnClose: Button? = null
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
        btnCopy = root.findViewById(R.id.btn_copy_search_link)
        btnFindStream = root.findViewById(R.id.btn_find_stream)
        btnPoster = root.findViewById(R.id.btn_poster_image)
        btnClose = root.findViewById<Button?>(R.id.btn_close_webview)
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

            override fun onPageStarted(view: WebView, url: String, favicon: Bitmap?) {
                lastPageUrl = url
                clientSideHistoryDepth = 0
                detectedPlaylistUrl = null
                detectedDownloadRequest = null
                updateBottomButtons(url)
                super.onPageStarted(view, url, favicon)
            }

            override fun onPageFinished(view: WebView, url: String) {
                super.onPageFinished(view, url)
                lastPageUrl = url
                installClientSideHistoryTracker()
                installPlaylistScanner()
                updateBottomButtons(url)
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
        webView.loadUrl(homeUrl)

        btnCopy.setOnClickListener {
            when (SearchWebViewButtonPolicy.resolve(webView.url, detectedPlaylistUrl != null).primaryAction) {
                SearchWebViewPrimaryAction.WATCH -> openConvertedCurrentUrl()
                SearchWebViewPrimaryAction.PRODUCT_CODE_SEARCH -> openProductCodeSearch()
                SearchWebViewPrimaryAction.NONE -> Unit
            }
        }
        btnFindStream.setOnClickListener {
            analyzeCurrentPageForPlaylist()
        }
        btnPoster.setOnClickListener {
            when (SearchWebViewButtonPolicy.resolve(webView.url, detectedPlaylistUrl != null).secondaryAction) {
                SearchWebViewSecondaryAction.POSTER -> showPosterImage()
                SearchWebViewSecondaryAction.DOWNLOAD -> showDetectedPlaylist()
                SearchWebViewSecondaryAction.NONE -> Unit
            }
        }
        btnClose?.setOnClickListener {
            onClose()
        }
        btnDownload.setOnClickListener {
            showDetectedPlaylist()
        }
        updateBottomButtons()
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
        ::webView.isInitialized &&
            SearchWebViewBackPolicy.resolve(
                nativeCanGoBack = webView.canGoBack(),
                clientSideHistoryDepth = clientSideHistoryDepth
            ) == SearchWebViewBackAction.WEB_VIEW_BACK

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

    private fun openConvertedCurrentUrl() {
        val convertedUrl = SearchLinkFormatter.toUpload18Url(webView.url)
        if (convertedUrl == null) {
            Log.d(HlsProbeDebugLog.TAG, HlsProbeDebugLog.line("copy-convert-failed", webView.url))
            Toast.makeText(activity, "detail 페이지에서만 복사할 수 있습니다.", Toast.LENGTH_SHORT).show()
            return
        }

        Log.d(HlsProbeDebugLog.TAG, HlsProbeDebugLog.line("copy-convert-success", convertedUrl))
        detectedPlaylistUrl = null
        detectedDownloadRequest = null
        debugRecorder.clear()
        btnDownload.visibility = View.GONE
        webView.loadUrl(convertedUrl)
        Toast.makeText(activity, "재생 페이지로 이동합니다.", Toast.LENGTH_SHORT).show()
    }

    private fun openProductCodeSearch() {
        val navigation = ProductCodeSearchNavigationPolicy.resolve()
        try {
            activity.startActivity(Intent(Intent.ACTION_VIEW, Uri.parse(navigation.url)))
        } catch (e: Exception) {
            Toast.makeText(activity, "브라우저를 열 수 없습니다: ${e.message ?: e.javaClass.simpleName}", Toast.LENGTH_SHORT).show()
        }
    }

    private fun handleObservedRequest(request: WebResourceRequest?) {
        val requestUrl = request?.url?.toString() ?: return
        debugRecorder.record("request", requestUrl)
        Log.d(
            HlsProbeDebugLog.TAG,
            HlsProbeDebugLog.line(
                phase = "webview-request",
                url = requestUrl,
                details = "method=${request.method} headers=${request.requestHeaders?.size ?: 0}"
            )
        )
        detectPlaylist(requestUrl)
        probeObservedRequest(requestUrl, request.requestHeaders.orEmpty())
    }

    private fun probeObservedRequest(requestUrl: String, requestHeaders: Map<String, String>) {
        if (!HlsRequestProbe.shouldInspectRequest(requestUrl)) {
            Log.d(HlsProbeDebugLog.TAG, HlsProbeDebugLog.line("probe-skip", requestUrl, "reason=filtered"))
            return
        }
        if (!probingUrls.add(requestUrl)) {
            Log.d(HlsProbeDebugLog.TAG, HlsProbeDebugLog.line("probe-skip", requestUrl, "reason=duplicate"))
            return
        }

        scope.launch {
            try {
                val pageUrl = lastPageUrl ?: webView.url
                val cookie = CookieManager.getInstance().getCookie(requestUrl)
                Log.d(
                    HlsProbeDebugLog.TAG,
                    HlsProbeDebugLog.line(
                        phase = "probe-start",
                        url = requestUrl,
                        details = "page=${HlsProbeDebugLog.shorten(pageUrl)} headers=${requestHeaders.size} cookie=${!cookie.isNullOrBlank()}"
                    )
                )
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
                    Log.d(
                        HlsProbeDebugLog.TAG,
                        HlsProbeDebugLog.line(
                            phase = "probe-found",
                            url = match.playlistUrl,
                            details = "reason=${match.reason}"
                        )
                    )
                    showPlaylist(
                        playlistUrl = match.playlistUrl,
                        pageUrl = pageUrl,
                        requestHeaders = requestHeaders,
                        cookie = cookie
                    )
                } else {
                    Log.d(HlsProbeDebugLog.TAG, HlsProbeDebugLog.line("probe-empty", requestUrl))
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
            Log.d(
                HlsProbeDebugLog.TAG,
                HlsProbeDebugLog.line("probe-open-failed", request.url, "error=${e.javaClass.simpleName}:${e.message.orEmpty()}")
            )
            return null
        }

        return try {
            val code = connection.responseCode
            val contentType = connection.contentType
            Log.d(
                HlsProbeDebugLog.TAG,
                HlsProbeDebugLog.line(
                    phase = "probe-response",
                    url = connection.url.toString(),
                    details = "code=$code type=${contentType ?: "unknown"}"
                )
            )
            if (code !in 200..399) {
                debugRecorder.record("probe-http-$code", request.url)
                Log.d(HlsProbeDebugLog.TAG, HlsProbeDebugLog.line("probe-reject", request.url, "reason=http-$code"))
                return null
            }

            val directMatch = HlsRequestProbe.detect(
                HlsProbeResponse(
                    requestUrl = connection.url.toString(),
                    contentType = contentType,
                    body = null
                )
            )
            if (directMatch != null) {
                Log.d(HlsProbeDebugLog.TAG, HlsProbeDebugLog.line("probe-direct-match", directMatch.playlistUrl, "reason=${directMatch.reason}"))
                return directMatch
            }

            val body = if (HlsRequestProbe.shouldReadBody(contentType)) {
                connection.inputStream.use { input ->
                    input.reader().readTextLimited(MAX_PROBE_BODY_CHARS)
                }
            } else {
                null
            }
            Log.d(
                HlsProbeDebugLog.TAG,
                HlsProbeDebugLog.line(
                    phase = "probe-body",
                    url = connection.url.toString(),
                    details = "read=${body != null} chars=${body?.length ?: 0}"
                )
            )
            HlsRequestProbe.detect(
                HlsProbeResponse(
                    requestUrl = connection.url.toString(),
                    contentType = contentType,
                    body = body
                )
            )
        } catch (e: Exception) {
            debugRecorder.record("probe-read-failed", "${request.url} (${e.javaClass.simpleName})")
            Log.d(
                HlsProbeDebugLog.TAG,
                HlsProbeDebugLog.line("probe-read-failed", request.url, "error=${e.javaClass.simpleName}:${e.message.orEmpty()}")
            )
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
        if (Build.VERSION.SDK_INT < Build.VERSION_CODES.N) {
            Log.d(HlsProbeDebugLog.TAG, "service-worker-probe disabled sdk=${Build.VERSION.SDK_INT}")
            return
        }
        Log.d(HlsProbeDebugLog.TAG, "service-worker-probe enabled")
        ServiceWorkerController.getInstance().setServiceWorkerClient(
            object : ServiceWorkerClient() {
                override fun shouldInterceptRequest(request: WebResourceRequest): WebResourceResponse? {
                    Log.d(
                        HlsProbeDebugLog.TAG,
                        HlsProbeDebugLog.line(
                            phase = "service-worker-request",
                            url = request.url?.toString(),
                            details = "method=${request.method} headers=${request.requestHeaders?.size ?: 0}"
                        )
                    )
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
            updateBottomButtons()
            if (SearchWebViewButtonPolicy.resolve(webView.url, detectedPlaylistUrl != null).secondaryAction == SearchWebViewSecondaryAction.DOWNLOAD) {
                Toast.makeText(activity, "m3u8 스트림을 감지했습니다.", Toast.LENGTH_SHORT).show()
            }
        }
    }

    private fun updateBottomButtons(currentUrl: String? = webView.url ?: lastPageUrl) {
        val state = SearchWebViewButtonPolicy.resolve(currentUrl, detectedPlaylistUrl != null)
        when (state.primaryAction) {
            SearchWebViewPrimaryAction.WATCH -> {
                btnCopy.text = "시청"
                btnCopy.visibility = View.VISIBLE
            }
            SearchWebViewPrimaryAction.PRODUCT_CODE_SEARCH -> {
                btnCopy.text = "품번찾기"
                btnCopy.visibility = View.VISIBLE
            }
            SearchWebViewPrimaryAction.NONE -> {
                btnCopy.visibility = View.GONE
            }
        }

        when (state.secondaryAction) {
            SearchWebViewSecondaryAction.POSTER -> {
                btnPoster.text = "표지"
                btnPoster.visibility = View.VISIBLE
            }
            SearchWebViewSecondaryAction.DOWNLOAD -> {
                btnPoster.text = "다운로드"
                btnPoster.visibility = View.VISIBLE
            }
            SearchWebViewSecondaryAction.NONE -> {
                btnPoster.visibility = View.GONE
            }
        }

        btnDownload.visibility = View.GONE
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
            activity.runOnUiThread {
                updateBottomButtons(url ?: webView.url ?: lastPageUrl)
            }
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

    private fun analyzeCurrentPageForPlaylist() {
        val pageUrl = webView.url
        if (pageUrl.isNullOrBlank()) {
            Toast.makeText(activity, "분석할 페이지 주소가 없습니다.", Toast.LENGTH_SHORT).show()
            return
        }

        btnFindStream.isEnabled = false
        Toast.makeText(activity, "m3u8 주소를 찾는 중입니다.", Toast.LENGTH_SHORT).show()
        dumpLiveWebViewState {
            startPagePlaylistLookup(pageUrl)
        }
    }

    private fun dumpLiveWebViewState(onComplete: () -> Unit) {
        webView.evaluateJavascript(
            """
            (function() {
              try {
                var lines = [];
                lines.push('href=' + location.href);
                lines.push('readyState=' + document.readyState);
                document.querySelectorAll('video').forEach(function(video, index) {
                  lines.push('video[' + index + '].src=' + (video.src || ''));
                  lines.push('video[' + index + '].currentSrc=' + (video.currentSrc || ''));
                  lines.push('video[' + index + '].networkState=' + video.networkState);
                  lines.push('video[' + index + '].readyState=' + video.readyState);
                });
                document.querySelectorAll('source, iframe').forEach(function(el, index) {
                  lines.push(el.tagName.toLowerCase() + '[' + index + '].src=' + (el.src || el.getAttribute('src') || ''));
                });
                if (window.performance && performance.getEntriesByType) {
                  performance.getEntriesByType('resource').slice(-80).forEach(function(entry, index) {
                    lines.push('resource[' + index + ']=' + entry.name);
                  });
                }
                return lines.join('\n');
              } catch (e) {
                return 'live dump error=' + e;
              }
            })();
            """.trimIndent()
        ) { value ->
            debugRecorder.record("live-dump", value)
            Log.d(HlsProbeDebugLog.TAG, "live-dump chars=${value?.length ?: 0}")
            detectPlaylist(value)
            onComplete()
        }
    }

    private fun startPagePlaylistLookup(pageUrl: String) {
        scope.launch {
            val result = withContext(Dispatchers.IO) {
                findPlaylistFromPage(pageUrl, pageUrl)
            }
            btnFindStream.isEnabled = true
            if (result.playlistUrl == null) {
                Log.d(HlsProbeDebugLog.TAG, "manual-find-empty reportChars=${result.report.length}")
                copyHlsLookupReport(result.report)
                Toast.makeText(activity, "m3u8 주소를 찾지 못했습니다. 진단 로그를 복사했습니다.", Toast.LENGTH_LONG).show()
            } else {
                Log.d(HlsProbeDebugLog.TAG, HlsProbeDebugLog.line("manual-find-found", result.playlistUrl))
                detectPlaylist(result.playlistUrl)
            }
        }
    }

    private fun findPlaylistFromPage(pageUrl: String, refererUrl: String): HlsLookupResult {
        val report = mutableListOf<String>()
        report += debugRecorder.snapshot()
        val html = fetchText(pageUrl, refererUrl, report)
            ?: return HlsLookupResult(null, report.joinToString("\n"))
        val firstAnalysis = HlsPageAnalyzer.analyze(pageUrl, html)
        report += "first follow urls: ${firstAnalysis.followUrls.size}"
        firstAnalysis.followUrls.forEachIndexed { index, followUrl ->
            report += "follow[$index]: $followUrl"
        }
        firstAnalysis.playlistUrl?.let {
            report += "playlist found in first page"
            return HlsLookupResult(it, report.joinToString("\n"))
        }

        val playlistUrl = firstAnalysis.followUrls.asSequence()
            .take(MAX_FOLLOW_URLS)
            .mapNotNull { followUrl ->
                val followText = fetchText(followUrl, pageUrl, report)
                if (followText == null) {
                    HlsStreamDetector.extractPlaylistUrl(followUrl)
                } else {
                    HlsPageAnalyzer.analyze(followUrl, followText).playlistUrl
                        ?: HlsStreamDetector.extractPlaylistUrl(followText)
                }
            }
            .firstOrNull()
        report += debugRecorder.snapshot()
        return HlsLookupResult(playlistUrl, report.joinToString("\n"))
    }

    private fun fetchText(url: String, refererUrl: String, report: MutableList<String>): String? {
        val connection = try {
            (URL(url).openConnection() as HttpURLConnection).apply {
                connectTimeout = 10_000
                readTimeout = 10_000
                instanceFollowRedirects = true
                setRequestProperty("User-Agent", WEB_USER_AGENT)
                setRequestProperty("Referer", refererUrl)
                CookieManager.getInstance().getCookie(url)?.let { cookies ->
                    setRequestProperty("Cookie", cookies)
                }
            }
        } catch (e: Exception) {
            report += "open failed: $url (${e.javaClass.simpleName})"
            Log.d(HlsProbeDebugLog.TAG, HlsProbeDebugLog.line("manual-open-failed", url, "error=${e.javaClass.simpleName}:${e.message.orEmpty()}"))
            return null
        }
        return try {
            val code = connection.responseCode
            val contentType = connection.contentType ?: "unknown"
            Log.d(HlsProbeDebugLog.TAG, HlsProbeDebugLog.line("manual-response", url, "code=$code type=$contentType"))
            if (code !in 200..399) {
                report += "fetch $code $contentType: $url"
                return null
            }
            val text = connection.inputStream.bufferedReader().use { it.readText() }
            report += "fetch $code $contentType ${text.length} chars: $url"
            text
        } catch (e: Exception) {
            report += "read failed: $url (${e.javaClass.simpleName})"
            null
        } finally {
            connection.disconnect()
        }
    }

    private fun copyHlsLookupReport(report: String) {
        val clipboard = activity.getSystemService(Context.CLIPBOARD_SERVICE) as ClipboardManager
        clipboard.setPrimaryClip(android.content.ClipData.newPlainText("hls lookup report", report))
    }

    private fun showPosterImage() {
        val poster = SearchPosterDisplayPolicy.resolve(webView.url)
        if (poster == null) {
            Toast.makeText(activity, "detail 페이지에서만 표지를 볼 수 있습니다.", Toast.LENGTH_SHORT).show()
            return
        }

        showPosterPopup(poster.posterUrl)
    }

    private fun showPosterPopup(posterUrl: String) {
        val dialog = Dialog(activity)
        val container = FrameLayout(activity).apply {
            setBackgroundColor(Color.argb(225, 0, 0, 0))
            setPadding(18, 18, 18, 18)
        }
        val image = ImageView(activity).apply {
            adjustViewBounds = true
            scaleType = ImageView.ScaleType.FIT_CENTER
            contentDescription = "poster"
        }
        container.addView(
            image,
            FrameLayout.LayoutParams(
                ViewGroup.LayoutParams.MATCH_PARENT,
                ViewGroup.LayoutParams.MATCH_PARENT,
                Gravity.CENTER
            )
        )
        container.setOnClickListener { dialog.dismiss() }
        image.setOnClickListener { dialog.dismiss() }
        dialog.setContentView(container)
        dialog.setCanceledOnTouchOutside(true)
        Glide.with(activity)
            .load(posterUrl)
            .fitCenter()
            .into(image)
        dialog.show()
        dialog.window?.setBackgroundDrawable(ColorDrawable(Color.TRANSPARENT))
        dialog.window?.setLayout(
            ViewGroup.LayoutParams.MATCH_PARENT,
            ViewGroup.LayoutParams.MATCH_PARENT
        )
    }

    companion object {
        const val WEB_USER_AGENT =
            "Mozilla/5.0 (Linux; Android 14) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125 Mobile Safari/537.36"
        private const val MAX_FOLLOW_URLS = 30
        private const val MAX_PROBE_BODY_CHARS = 256_000
        private const val PROBE_CONNECT_TIMEOUT_MS = 8_000
        private const val PROBE_READ_TIMEOUT_MS = 8_000
    }

    private data class HlsLookupResult(
        val playlistUrl: String?,
        val report: String
    )
}
