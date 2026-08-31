package com.kys.videomanager.browser

import android.content.Context
import android.content.SharedPreferences

/**
 * 브라우저 즐겨찾기 / 마지막 접속 주소를 SharedPreferences에 저장하는 싱글톤.
 * VideoPreferenceManager와 동일한 init(context) 패턴을 따른다.
 */
object BrowserPreferenceManager {

    private const val PREF_NAME = "browser_prefs"
    private const val KEY_FAVORITES = "favorites"
    private const val KEY_LAST_VISITED_URL = "last_visited_url"
    private const val KEY_LAST_VISITED_TITLE = "last_visited_title"

    private lateinit var prefs: SharedPreferences

    fun init(context: Context) {
        prefs = context.applicationContext
            .getSharedPreferences(PREF_NAME, Context.MODE_PRIVATE)
    }

    // --- 즐겨찾기 ---------------------------------------------------------------

    fun getFavorites(): List<BrowserFavorite> {
        val json = prefs.getString(KEY_FAVORITES, null) ?: return emptyList()
        return try {
            deserializeFavorites(json)
        } catch (_: org.json.JSONException) {
            emptyList()
        }
    }

    fun addFavorite(favorite: BrowserFavorite) {
        val updated = getFavorites().filterNot { it.url == favorite.url } + favorite
        prefs.edit().putString(KEY_FAVORITES, serializeFavorites(updated)).apply()
    }

    fun removeFavorite(url: String) {
        val updated = getFavorites().filterNot { it.url == url }
        prefs.edit().putString(KEY_FAVORITES, serializeFavorites(updated)).apply()
    }

    fun isFavorite(url: String): Boolean =
        getFavorites().any { it.url == url }

    // --- 마지막 접속 주소 ---------------------------------------------------------

    fun saveLastVisited(url: String, title: String) {
        prefs.edit()
            .putString(KEY_LAST_VISITED_URL, url)
            .putString(KEY_LAST_VISITED_TITLE, title)
            .apply()
    }

    fun getLastVisitedUrl(): String? = prefs.getString(KEY_LAST_VISITED_URL, null)

    fun getLastVisitedTitle(): String? = prefs.getString(KEY_LAST_VISITED_TITLE, null)
}
