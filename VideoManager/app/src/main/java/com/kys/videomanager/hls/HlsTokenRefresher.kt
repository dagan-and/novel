package com.kys.videomanager.hls
import com.kys.videomanager.hlsplaylist.HlsPlaylistProbeSession

import android.content.Context
import android.util.Log
import android.webkit.WebView
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.suspendCancellableCoroutine
import kotlinx.coroutines.withContext
import kotlinx.coroutines.withTimeoutOrNull
import kotlin.coroutines.resume

data class HlsRefreshedSession(
    val playlistUrl: String,
    val requestHeaders: Map<String, String>,
    val cookie: String?
)

/**
 * Re-opens a video's page in a headless (never attached to any window/Activity) WebView to
 * obtain a freshly signed HLS playlist URL when the original one has been rejected by the CDN
 * (401/403/410). Runs entirely inside whatever process already hosts it (the foreground download
 * service) — no Activity is launched, so this works even while the app has no visible UI.
 */
class HlsTokenRefresher(private val context: Context) {

    suspend fun refresh(pageUrl: String): HlsRefreshedSession? =
        withContext(Dispatchers.Main) {
            withTimeoutOrNull(REFRESH_TIMEOUT_MS) {
                awaitRefresh(pageUrl)
            }
        }

    private suspend fun awaitRefresh(pageUrl: String): HlsRefreshedSession =
        suspendCancellableCoroutine { continuation ->
            val webView = WebView(context.applicationContext)
            var session: HlsPlaylistProbeSession? = null
            var finished = false

            fun finish(result: HlsRefreshedSession) {
                if (finished) return
                finished = true
                session?.close()
                webView.destroy()
                if (continuation.isActive) {
                    continuation.resume(result)
                }
            }

            continuation.invokeOnCancellation {
                if (!finished) {
                    finished = true
                    session?.close()
                    webView.destroy()
                }
            }

            Log.d(DEBUG_TAG, "token-refresh-start pageUrl=$pageUrl")
            session = HlsPlaylistProbeSession(webView) { playlistUrl, headers, cookie ->
                Log.d(DEBUG_TAG, "token-refresh-found playlistUrl=$playlistUrl")
                finish(HlsRefreshedSession(playlistUrl, headers, cookie))
            }
            session.attachAndLoad(pageUrl)
        }

    companion object {
        private const val DEBUG_TAG = "DDDDD"
        private const val REFRESH_TIMEOUT_MS = 20_000L
    }
}
