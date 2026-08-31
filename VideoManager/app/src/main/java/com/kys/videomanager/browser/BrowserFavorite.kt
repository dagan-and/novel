package com.kys.videomanager.browser

import org.json.JSONArray
import org.json.JSONObject

data class BrowserFavorite(
    val url: String,
    val title: String
)

fun serializeFavorites(favorites: List<BrowserFavorite>): String {
    val array = JSONArray()
    favorites.forEach { favorite ->
        val entry = JSONObject()
        entry.put("url", favorite.url)
        entry.put("title", favorite.title)
        array.put(entry)
    }
    return array.toString()
}

fun deserializeFavorites(json: String): List<BrowserFavorite> {
    val array = JSONArray(json)
    return (0 until array.length()).mapNotNull { index ->
        val entry = array.optJSONObject(index) ?: return@mapNotNull null
        val url = entry.optString("url", "")
        if (url.isBlank()) return@mapNotNull null
        BrowserFavorite(url = url, title = entry.optString("title", url))
    }
}
