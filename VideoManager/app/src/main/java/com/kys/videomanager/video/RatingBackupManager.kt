package com.kys.videomanager.video

import android.content.ContentUris
import android.content.ContentValues
import android.content.Context
import android.content.pm.PackageManager
import android.net.Uri
import android.os.Build
import android.os.Environment
import android.provider.MediaStore
import android.util.Log
import androidx.annotation.RequiresApi
import androidx.core.content.ContextCompat
import kotlinx.coroutines.CoroutineScope
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.SupervisorJob
import kotlinx.coroutines.launch
import kotlinx.coroutines.sync.Mutex
import kotlinx.coroutines.sync.withLock
import kotlinx.coroutines.withContext
import org.json.JSONObject
import java.io.File

private const val TAG = "RatingBackupManager"
private const val BACKUP_DIR_NAME = "VideoManager"
private const val BACKUP_FILE_NAME = "video_ratings_backup.json"
private const val BACKUP_VERSION = 1
private const val STATE_PREF_NAME = "rating_backup_state"
private const val KEY_BOOTSTRAPPED = "bootstrapped"

data class BackupData(
    val ratings: Map<String, Float>,
    val defaultPlayerPackage: String?,
    val defaultPlayerName: String?
)

fun serializeBackup(data: BackupData): String {
    val root = JSONObject()
    root.put("version", BACKUP_VERSION)

    val ratingsJson = JSONObject()
    data.ratings.forEach { (path, rating) -> ratingsJson.put(path, rating.toDouble()) }
    root.put("ratings", ratingsJson)

    if (data.defaultPlayerPackage != null) {
        val playerJson = JSONObject()
        playerJson.put("packageName", data.defaultPlayerPackage)
        playerJson.put("appName", data.defaultPlayerName ?: "")
        root.put("defaultPlayer", playerJson)
    } else {
        root.put("defaultPlayer", JSONObject.NULL)
    }

    return root.toString()
}

fun deserializeBackup(json: String): BackupData {
    val root = JSONObject(json)

    val ratingsJson = root.optJSONObject("ratings") ?: JSONObject()
    val ratings = mutableMapOf<String, Float>()
    val keys = ratingsJson.keys()
    while (keys.hasNext()) {
        val key = keys.next()
        ratings[key] = ratingsJson.getDouble(key).toFloat()
    }

    val playerJson = root.optJSONObject("defaultPlayer")
    val pkg = playerJson?.optString("packageName")?.takeIf { it.isNotEmpty() }
    val name = playerJson?.optString("appName")?.takeIf { it.isNotEmpty() }

    return BackupData(ratings = ratings, defaultPlayerPackage = pkg, defaultPlayerName = name)
}

object RatingBackupManager {

    private lateinit var appContext: Context
    private val scope = CoroutineScope(Dispatchers.IO + SupervisorJob())
    private val exportMutex = Mutex()

    fun init(context: Context) {
        appContext = context.applicationContext
    }

    private fun statePrefs() = appContext.getSharedPreferences(STATE_PREF_NAME, Context.MODE_PRIVATE)

    /**
     * 현재 별점 + 기본 플레이어 정보를 백업 파일에 덮어쓴다. Fire-and-forget, 실패해도 크래시 없음.
     * exportMutex로 직렬화하여, 연달아 여러 번 호출돼도 파일 쓰기가 동시에 겹치지 않게 한다.
     */
    fun scheduleExport() {
        scope.launch {
            try {
                exportMutex.withLock { exportNow() }
            } catch (e: Exception) {
                Log.w(TAG, "백업 내보내기 실패", e)
            }
        }
    }

    /**
     * 로컬 데이터가 완전히 비어있고, 이 설치에서 아직 한 번도 초기화되지 않았을 때만 복원한다.
     * "bootstrapped" 플래그는 앱 데이터 초기화/재설치 시 함께 사라지므로, 진짜 재설치(플래그도
     * 없음)와 같은 설치 내에서 사용자가 별점을 전부 지운 경우(플래그는 남아있음)를 구분해준다 —
     * 후자의 경우 복원을 건너뛰어 지운 별점이 옛 백업으로 되살아나는 것을 막는다.
     * @return 복원이 실제로 일어났는지
     */
    suspend fun restoreIfLocalEmpty(): Boolean = withContext(Dispatchers.IO) {
        val hasLocalData = VideoPreferenceManager.getAllRatings().isNotEmpty() ||
            VideoPreferenceManager.getDefaultPlayerPackage() != null
        val alreadyBootstrapped = statePrefs().getBoolean(KEY_BOOTSTRAPPED, false)
        statePrefs().edit().putBoolean(KEY_BOOTSTRAPPED, true).apply()

        if (hasLocalData || alreadyBootstrapped) return@withContext false

        try {
            val json = readBackupFile() ?: return@withContext false
            val data = deserializeBackup(json)
            if (data.ratings.isEmpty() && data.defaultPlayerPackage == null) return@withContext false

            data.ratings.forEach { (path, rating) -> VideoPreferenceManager.saveRating(path, rating) }
            if (data.defaultPlayerPackage != null) {
                VideoPreferenceManager.saveDefaultPlayer(data.defaultPlayerPackage, data.defaultPlayerName ?: "")
            }
            true
        } catch (e: Exception) {
            Log.w(TAG, "백업 복원 실패", e)
            false
        }
    }

    private fun exportNow() {
        val data = BackupData(
            ratings = VideoPreferenceManager.getAllRatings(),
            defaultPlayerPackage = VideoPreferenceManager.getDefaultPlayerPackage(),
            defaultPlayerName = VideoPreferenceManager.getDefaultPlayerName()
        )
        val json = serializeBackup(data)

        when {
            Build.VERSION.SDK_INT >= Build.VERSION_CODES.R && canAccessLegacyFile() -> writeViaLegacyFile(json)
            Build.VERSION.SDK_INT >= Build.VERSION_CODES.Q -> writeViaMediaStore(json)
            canAccessLegacyFile() -> writeViaLegacyFile(json)
            else -> Log.w(TAG, "파일 접근 권한 없음 - 백업 스킵")
        }
    }

    private fun readBackupFile(): String? = when {
        Build.VERSION.SDK_INT >= Build.VERSION_CODES.R && canAccessLegacyFile() -> readViaLegacyFile()
        Build.VERSION.SDK_INT >= Build.VERSION_CODES.Q -> readViaMediaStore()
        canAccessLegacyFile() -> readViaLegacyFile()
        else -> null
    }

    /**
     * API 30+에서는 MediaStore.Downloads의 "자기 파일 소유권" 인식이 pm clear/재설치 후
     * 리셋되어(FUSE 소유권 캐시가 초기화됨) 자기가 만든 백업 파일조차 다시 쿼리하지 못하는
     * 문제가 실기기(Android 13)에서 확인됨. MANAGE_EXTERNAL_STORAGE로 소유권과 무관하게
     * 직접 파일 접근하여 이 문제를 회피한다.
     */
    private fun canAccessLegacyFile(): Boolean =
        if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.R) {
            Environment.isExternalStorageManager()
        } else {
            hasLegacyWritePermission()
        }

    // --- API 29(Q) 전용 : MediaStore.Downloads ---------------------------------

    private fun relativePath() = Environment.DIRECTORY_DOWNLOADS + "/$BACKUP_DIR_NAME/"

    @RequiresApi(Build.VERSION_CODES.Q)
    private fun findBackupUri(): Uri? {
        val collection = MediaStore.Downloads.EXTERNAL_CONTENT_URI
        val projection = arrayOf(MediaStore.Downloads._ID)
        val selection = "${MediaStore.Downloads.DISPLAY_NAME} = ? AND ${MediaStore.Downloads.RELATIVE_PATH} = ?"
        val args = arrayOf(BACKUP_FILE_NAME, relativePath())

        appContext.contentResolver.query(collection, projection, selection, args, null)?.use { cursor ->
            if (cursor.moveToFirst()) {
                val id = cursor.getLong(cursor.getColumnIndexOrThrow(MediaStore.Downloads._ID))
                return ContentUris.withAppendedId(collection, id)
            }
        }
        return null
    }

    @RequiresApi(Build.VERSION_CODES.Q)
    private fun writeViaMediaStore(json: String) {
        val resolver = appContext.contentResolver
        val uri = findBackupUri() ?: run {
            val values = ContentValues().apply {
                put(MediaStore.Downloads.DISPLAY_NAME, BACKUP_FILE_NAME)
                put(MediaStore.Downloads.MIME_TYPE, "application/json")
                put(MediaStore.Downloads.RELATIVE_PATH, relativePath())
            }
            resolver.insert(MediaStore.Downloads.EXTERNAL_CONTENT_URI, values)
                ?: throw IllegalStateException("백업 파일 생성 실패")
        }

        resolver.openOutputStream(uri, "wt")?.use { it.write(json.toByteArray()) }
            ?: throw IllegalStateException("백업 파일 열기 실패")
    }

    @RequiresApi(Build.VERSION_CODES.Q)
    private fun readViaMediaStore(): String? {
        val uri = findBackupUri() ?: return null
        return appContext.contentResolver.openInputStream(uri)?.use { it.readBytes().decodeToString() }
    }

    // --- API 21~28 : 공용 Downloads 디렉터리 직접 접근 (WRITE_EXTERNAL_STORAGE) ---
    // --- API 30+   : 공용 Downloads 디렉터리 직접 접근 (MANAGE_EXTERNAL_STORAGE) --

    private fun legacyFile(): File {
        val dir = File(Environment.getExternalStoragePublicDirectory(Environment.DIRECTORY_DOWNLOADS), BACKUP_DIR_NAME)
        if (!dir.exists()) dir.mkdirs()
        return File(dir, BACKUP_FILE_NAME)
    }

    private fun hasLegacyWritePermission(): Boolean =
        ContextCompat.checkSelfPermission(appContext, android.Manifest.permission.WRITE_EXTERNAL_STORAGE) ==
            PackageManager.PERMISSION_GRANTED

    private fun writeViaLegacyFile(json: String) {
        legacyFile().writeText(json)
    }

    private fun readViaLegacyFile(): String? {
        val file = legacyFile()
        return if (file.exists()) file.readText() else null
    }
}
