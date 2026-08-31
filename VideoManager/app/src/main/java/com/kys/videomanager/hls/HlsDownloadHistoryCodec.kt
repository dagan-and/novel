package com.kys.videomanager.hls

import org.json.JSONArray
import org.json.JSONObject

object HlsDownloadHistoryCodec {
    fun encode(progresses: List<HlsDownloadProgress>): String {
        val root = JSONObject()
        val rows = JSONArray()
        progresses.forEach { progress ->
            rows.put(progress.toJson())
        }
        root.put("downloads", rows)
        return root.toString()
    }

    fun decode(text: String): List<HlsDownloadProgress> {
        val rows = JSONObject(text).optJSONArray("downloads") ?: return emptyList()
        return buildList {
            for (index in 0 until rows.length()) {
                val row = rows.optJSONObject(index) ?: continue
                val progress = runCatching { row.toProgress() }.getOrNull() ?: continue
                add(progress)
            }
        }
    }

    private fun HlsDownloadProgress.toJson(): JSONObject =
        JSONObject()
            .put("id", id)
            .put("status", status.name)
            .put("title", title)
            .put("playlistUrl", playlistUrl)
            .put("downloadedSegments", downloadedSegments)
            .put("totalSegments", totalSegments)
            .put("downloadedBytes", downloadedBytes)
            .put("outputPath", outputPath)
            .put("message", message)
            .put("request", request?.toJson())

    private fun HlsDownloadRequest.toJson(): JSONObject {
        val headerJson = JSONObject()
        requestHeaders.forEach { (key, value) -> headerJson.put(key, value) }
        return JSONObject()
            .put("id", id)
            .put("playlistUrl", playlistUrl)
            .put("pageUrl", pageUrl)
            .put("requestHeaders", headerJson)
            .put("cookie", cookie)
            .put("title", title)
    }

    private fun JSONObject.toProgress(): HlsDownloadProgress {
        val id = getString("id")
        val statusName = getString("status")
        val title = getString("title")
        val playlistUrl = getString("playlistUrl")
        return HlsDownloadProgress(
            id = id,
            status = runCatching { HlsDownloadStatus.valueOf(statusName) }
                .getOrDefault(HlsDownloadStatus.FAILED),
            title = title,
            playlistUrl = playlistUrl,
            downloadedSegments = optInt("downloadedSegments"),
            totalSegments = optInt("totalSegments"),
            downloadedBytes = optLong("downloadedBytes"),
            outputPath = optNullableString("outputPath"),
            message = optString("message", "대기 중"),
            request = optJSONObject("request")?.toRequest()
        )
    }

    private fun JSONObject.toRequest(): HlsDownloadRequest {
        val headers = linkedMapOf<String, String>()
        val headerJson = optJSONObject("requestHeaders") ?: JSONObject()
        headerJson.keys().forEach { key ->
            headers[key] = headerJson.optString(key)
        }
        return HlsDownloadRequest(
            id = getString("id"),
            playlistUrl = getString("playlistUrl"),
            pageUrl = optNullableString("pageUrl"),
            requestHeaders = headers,
            cookie = optNullableString("cookie"),
            title = optString("title")
        )
    }

    private fun JSONObject.optNullableString(name: String): String? =
        if (isNull(name)) null else optString(name)
}
