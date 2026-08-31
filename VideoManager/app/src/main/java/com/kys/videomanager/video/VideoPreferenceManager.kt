package com.kys.videomanager.video

import android.content.Context
import android.content.SharedPreferences

/**
 * 영상 별점을 SharedPreferences에 저장/불러오는 싱글톤
 *
 * 사용법:
 *   1. Application.onCreate() 또는 MainActivity.onCreate() 최초 1회 init(context) 호출
 *   2. saveRating(fileName, rating) / getRating(fileName) 로 읽기·쓰기
 *
 * 키(Key)   : 영상 파일명 (e.g. "video.mp4")
 * 값(Value) : Float 별점 (0.0 ~ 5.0)
 */
object VideoPreferenceManager {

    private const val PREF_NAME = "video_ratings"

    // 기본 플레이어 저장 키
    private const val KEY_PLAYER_PKG  = "default_player_package"
    private const val KEY_PLAYER_NAME = "default_player_name"
    private const val KEY_RATING_FILTER = "selected_rating_filter"
    private const val KEY_LAST_PLAYED_PATH = "last_played_path"

    private lateinit var prefs: SharedPreferences

    // --- 초기화 ----------------------------------------------------------------

    /**
     * Activity/Application 컨텍스트로 초기화.
     * 반드시 사용 전에 한 번 호출해야 합니다.
     */
    fun init(context: Context) {
        prefs = context.applicationContext
            .getSharedPreferences(PREF_NAME, Context.MODE_PRIVATE)
    }

    // --- 읽기 / 쓰기 ----------------------------------------------------------

    /**
     * 별점 저장
     * @param filePath  영상 파일명 (키)
     * @param rating    저장할 별점 (값)
     */
    fun saveRating(filePath: String, rating: Float) {
        prefs.edit().putFloat(filePath, rating).apply()
    }

    /**
     * 별점 불러오기
     * @param filePath  영상 파일명 (키)
     * @return 저장된 별점, 없으면 0.0f
     */
    fun getRating(filePath: String): Float {
        return prefs.getFloat(filePath, 0f)
    }

    /**
     * 저장된 모든 별점 맵 반환
     * (백업·디버그 용도로 활용 가능)
     */
    fun getAllRatings(): Map<String, Float> {
        @Suppress("UNCHECKED_CAST")
        return prefs.all
            .filterValues { it is Float }
            .mapValues { it.value as Float }
    }

    /**
     * 특정 영상의 별점 삭제
     */
    fun deleteRating(filePath: String) {
        prefs.edit().remove(filePath).apply()
    }

    /**
     * 모든 별점 초기화
     */
    fun clearAll() {
        prefs.edit().clear().apply()
    }

    // --- 별점 필터 ---------------------------------------------------------------

    fun saveRatingFilter(filter: RatingFilter) {
        prefs.edit()
            .putString(KEY_RATING_FILTER, filter.toPreferenceValue())
            .apply()
    }

    fun getRatingFilter(): RatingFilter =
        ratingFilterFromPreferenceValue(prefs.getString(KEY_RATING_FILTER, null))

    // --- 기본 플레이어 ---------------------------------------------------------

    /**
     * 기본 동영상 플레이어 앱 저장
     * @param packageName  앱 패키지명 (예: "com.mxtech.videoplayer.ad")
     * @param appName      사용자에게 표시할 앱 이름 (예: "MX Player")
     */
    fun saveDefaultPlayer(packageName: String, appName: String) {
        prefs.edit()
            .putString(KEY_PLAYER_PKG, packageName)
            .putString(KEY_PLAYER_NAME, appName)
            .apply()
    }

    /** 저장된 기본 플레이어 패키지명 반환. 없으면 null */
    fun getDefaultPlayerPackage(): String? = prefs.getString(KEY_PLAYER_PKG, null)

    /** 저장된 기본 플레이어 앱 이름 반환. 없으면 null */
    fun getDefaultPlayerName(): String? = prefs.getString(KEY_PLAYER_NAME, null)

    /** 기본 플레이어 설정 초기화 */
    fun clearDefaultPlayer() {
        prefs.edit()
            .remove(KEY_PLAYER_PKG)
            .remove(KEY_PLAYER_NAME)
            .apply()
    }

    // --- 최근 재생 ---------------------------------------------------------------

    /** 가장 최근 재생을 시도한 영상의 절대 경로 저장 (단일 슬롯) */
    fun saveLastPlayed(path: String) {
        prefs.edit().putString(KEY_LAST_PLAYED_PATH, path).apply()
    }

    /** 가장 최근 재생을 시도한 영상의 절대 경로 반환. 없으면 null */
    fun getLastPlayedPath(): String? = prefs.getString(KEY_LAST_PLAYED_PATH, null)
}
