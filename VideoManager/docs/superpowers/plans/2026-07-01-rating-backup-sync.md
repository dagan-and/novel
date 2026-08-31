# 별점/설정 자동 백업 (공용 저장소 JSON 동기화) Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 영상 별점/기본 플레이어 설정을 공용 저장소(Downloads) JSON 파일에 자동 동기화하여, 앱 삭제 후 재설치해도 복원할 수 있게 한다.

**Architecture:** 신규 `RatingBackupManager` object가 `VideoPreferenceManager`의 데이터를 읽어 JSON으로 직렬화하고, API 29+에서는 `MediaStore.Downloads`, API 21~28에서는 공용 Downloads 디렉터리에 직접 파일 I/O로 저장한다. `MainActivity`의 각 데이터 변경 지점에서 export를 트리거하고, `onCreate`에서 로컬 데이터가 비어있을 때만 복원을 시도한다.

**Tech Stack:** Kotlin, `org.json` (Android SDK 내장, 추가 의존성 없음), Kotlin Coroutines, `MediaStore.Downloads` (API 29+), `java.io.File` (API 21~28)

## Global Constraints

- minSdk 21, targetSdk 34, compileSdk 34 (기존 `app/build.gradle` 값 유지)
- 백업 파일 경로: `Downloads/VideoManager/video_ratings_backup.json` (고정, 버전 파일 없음)
- API 21~28에서 `WRITE_EXTERNAL_STORAGE` 권한이 없으면 새 권한 팝업을 띄우지 않고 조용히 백업을 스킵한다
- 모든 백업 I/O는 예외를 앱 밖으로 전파하지 않는다 (try/catch + `Log.w`)
- `VideoPreferenceManager.kt`는 수정하지 않는다 (기존 스펙 결정)

---

### Task 1: 백업 데이터 직렬화/역직렬화 (순수 함수 + 단위 테스트)

**Files:**
- Create: `app/src/main/java/com/example/videomanager/RatingBackupManager.kt`
- Test: `app/src/test/java/com/example/videomanager/RatingBackupSerializationTest.kt`

**Interfaces:**
- Produces: `data class BackupData(val ratings: Map<String, Float>, val defaultPlayerPackage: String?, val defaultPlayerName: String?)`
- Produces: `fun serializeBackup(data: BackupData): String`
- Produces: `fun deserializeBackup(json: String): BackupData` (malformed JSON이면 `org.json.JSONException` 던짐)

- [ ] **Step 1: 실패하는 테스트 작성**

`app/src/test/java/com/example/videomanager/RatingBackupSerializationTest.kt` 생성:

```kotlin
package com.example.videomanager

import org.json.JSONException
import org.junit.Assert.assertEquals
import org.junit.Assert.assertNull
import org.junit.Assert.assertTrue
import org.junit.Test

class RatingBackupSerializationTest {

    @Test fun `round trip preserves ratings and default player`() {
        val original = BackupData(
            ratings = mapOf("/a.mp4" to 4.5f, "/b.mp4" to 3.0f),
            defaultPlayerPackage = "com.mxtech.videoplayer.ad",
            defaultPlayerName = "MX Player"
        )

        val restored = deserializeBackup(serializeBackup(original))

        assertEquals(original.ratings, restored.ratings)
        assertEquals(original.defaultPlayerPackage, restored.defaultPlayerPackage)
        assertEquals(original.defaultPlayerName, restored.defaultPlayerName)
    }

    @Test fun `empty ratings and null default player round trip`() {
        val original = BackupData(ratings = emptyMap(), defaultPlayerPackage = null, defaultPlayerName = null)

        val restored = deserializeBackup(serializeBackup(original))

        assertTrue(restored.ratings.isEmpty())
        assertNull(restored.defaultPlayerPackage)
        assertNull(restored.defaultPlayerName)
    }

    @Test(expected = JSONException::class)
    fun `malformed json throws`() {
        deserializeBackup("not a json")
    }

    @Test fun `missing defaultPlayer key parses as null`() {
        val json = """{"version":1,"ratings":{"/a.mp4":5.0}}"""

        val restored = deserializeBackup(json)

        assertEquals(5.0f, restored.ratings["/a.mp4"])
        assertNull(restored.defaultPlayerPackage)
    }
}
```

- [ ] **Step 2: 테스트 실행하여 실패 확인**

Run: `./gradlew testDebugUnitTest --tests "com.example.videomanager.RatingBackupSerializationTest"`
Expected: FAIL (컴파일 에러 — `BackupData`, `serializeBackup`, `deserializeBackup` 미정의)

- [ ] **Step 3: 최소 구현 작성**

`app/src/main/java/com/example/videomanager/RatingBackupManager.kt` 생성 (이 태스크에서는 아래 부분만 작성):

```kotlin
package com.example.videomanager

import org.json.JSONObject

private const val BACKUP_VERSION = 1

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
```

- [ ] **Step 4: 테스트 실행하여 통과 확인**

Run: `./gradlew testDebugUnitTest --tests "com.example.videomanager.RatingBackupSerializationTest"`
Expected: PASS (4 tests)

- [ ] **Step 5: 커밋**

```bash
git add app/src/main/java/com/example/videomanager/RatingBackupManager.kt app/src/test/java/com/example/videomanager/RatingBackupSerializationTest.kt
git commit -m "feat: add rating backup JSON serialization"
```

(이 프로젝트는 git 저장소가 아니므로, 실제 커밋 대신 변경 사항을 그대로 두고 다음 태스크로 진행해도 됨)

---

### Task 2: 공용 저장소 I/O (`RatingBackupManager` 나머지 구현)

**Files:**
- Modify: `app/src/main/java/com/example/videomanager/RatingBackupManager.kt` (Task 1에서 만든 파일에 이어서 작성)

**Interfaces:**
- Consumes: `BackupData`, `serializeBackup`, `deserializeBackup` (Task 1)
- Consumes: `VideoPreferenceManager.getAllRatings(): Map<String, Float>`, `getDefaultPlayerPackage(): String?`, `getDefaultPlayerName(): String?`, `saveRating(String, Float)`, `saveDefaultPlayer(String, String)`
- Produces: `object RatingBackupManager { fun init(context: Context); fun scheduleExport(); suspend fun restoreIfLocalEmpty(): Boolean }`

이 태스크는 Android 프레임워크 I/O(MediaStore, 파일 시스템)에 의존하므로 JVM 단위 테스트로 검증할 수 없다. Task 4의 수동 QA로 검증한다.

- [ ] **Step 1: `RatingBackupManager` object 추가**

`app/src/main/java/com/example/videomanager/RatingBackupManager.kt` 상단 import를 아래로 교체하고, 파일 맨 아래에 object를 추가한다:

```kotlin
package com.example.videomanager

import android.content.ContentUris
import android.content.ContentValues
import android.content.Context
import android.content.pm.PackageManager
import android.net.Uri
import android.os.Build
import android.os.Environment
import android.provider.MediaStore
import android.util.Log
import androidx.core.content.ContextCompat
import kotlinx.coroutines.CoroutineScope
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.SupervisorJob
import kotlinx.coroutines.launch
import kotlinx.coroutines.withContext
import org.json.JSONObject
import java.io.File

private const val TAG = "RatingBackupManager"
private const val BACKUP_DIR_NAME = "VideoManager"
private const val BACKUP_FILE_NAME = "video_ratings_backup.json"
private const val BACKUP_VERSION = 1

// ... BackupData, serializeBackup, deserializeBackup는 Task 1에서 작성한 그대로 유지 ...

object RatingBackupManager {

    private lateinit var appContext: Context
    private val scope = CoroutineScope(Dispatchers.IO + SupervisorJob())

    fun init(context: Context) {
        appContext = context.applicationContext
    }

    /** 현재 별점 + 기본 플레이어 정보를 백업 파일에 덮어쓴다. Fire-and-forget, 실패해도 크래시 없음. */
    fun scheduleExport() {
        scope.launch {
            try {
                exportNow()
            } catch (e: Exception) {
                Log.w(TAG, "백업 내보내기 실패", e)
            }
        }
    }

    /** 로컬 데이터가 완전히 비어있을 때만 백업 파일에서 복원한다. @return 복원이 실제로 일어났는지 */
    suspend fun restoreIfLocalEmpty(): Boolean = withContext(Dispatchers.IO) {
        val hasLocalData = VideoPreferenceManager.getAllRatings().isNotEmpty() ||
            VideoPreferenceManager.getDefaultPlayerPackage() != null
        if (hasLocalData) return@withContext false

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

        if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.Q) {
            writeViaMediaStore(json)
        } else {
            writeViaLegacyFile(json)
        }
    }

    private fun readBackupFile(): String? {
        return if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.Q) {
            readViaMediaStore()
        } else {
            readViaLegacyFile()
        }
    }

    // --- API 29+ : MediaStore.Downloads ---------------------------------------

    private fun relativePath() = Environment.DIRECTORY_DOWNLOADS + "/$BACKUP_DIR_NAME/"

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

    private fun readViaMediaStore(): String? {
        val uri = findBackupUri() ?: return null
        return appContext.contentResolver.openInputStream(uri)?.use { it.readBytes().decodeToString() }
    }

    // --- API 21~28 : 공용 Downloads 디렉터리 직접 접근 ---------------------------

    private fun legacyFile(): File {
        val dir = File(Environment.getExternalStoragePublicDirectory(Environment.DIRECTORY_DOWNLOADS), BACKUP_DIR_NAME)
        if (!dir.exists()) dir.mkdirs()
        return File(dir, BACKUP_FILE_NAME)
    }

    private fun hasLegacyWritePermission(): Boolean =
        ContextCompat.checkSelfPermission(appContext, android.Manifest.permission.WRITE_EXTERNAL_STORAGE) ==
            PackageManager.PERMISSION_GRANTED

    private fun writeViaLegacyFile(json: String) {
        if (!hasLegacyWritePermission()) {
            Log.w(TAG, "WRITE_EXTERNAL_STORAGE 권한 없음 - 백업 스킵")
            return
        }
        legacyFile().writeText(json)
    }

    private fun readViaLegacyFile(): String? {
        if (!hasLegacyWritePermission()) return null
        val file = legacyFile()
        return if (file.exists()) file.readText() else null
    }
}
```

- [ ] **Step 2: 프로젝트 빌드 확인**

Run: `./gradlew :app:compileDebugKotlin`
Expected: BUILD SUCCESSFUL (컴파일 에러 없음)

- [ ] **Step 3: 커밋**

```bash
git add app/src/main/java/com/example/videomanager/RatingBackupManager.kt
git commit -m "feat: add public storage I/O for rating backup"
```

(git 저장소가 아니므로 실제 커밋은 생략 가능)

---

### Task 3: `MainActivity` 연동 (export 트리거 + 시작 시 복원)

**Files:**
- Modify: `app/src/main/java/com/example/videomanager/MainActivity.kt`

**Interfaces:**
- Consumes: `RatingBackupManager.init(Context)`, `RatingBackupManager.scheduleExport()`, `RatingBackupManager.restoreIfLocalEmpty(): Boolean` (Task 2)

- [ ] **Step 1: `onCreate`에서 초기화 순서 변경 — 복원을 영상 로딩보다 먼저 완료**

`app/src/main/java/com/example/videomanager/MainActivity.kt:109-116`의 기존 코드:

```kotlin
    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        setContentView(R.layout.activity_main)

        VideoPreferenceManager.init(this)
        initViews()
        checkPermissionAndLoad()
    }
```

다음으로 교체:

```kotlin
    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        setContentView(R.layout.activity_main)

        VideoPreferenceManager.init(this)
        RatingBackupManager.init(this)
        initViews()

        scope.launch {
            val restored = RatingBackupManager.restoreIfLocalEmpty()
            if (restored) {
                Toast.makeText(this@MainActivity, "이전 데이터를 백업에서 복원했습니다.", Toast.LENGTH_SHORT).show()
            }
            checkPermissionAndLoad()
        }
    }
```

- [ ] **Step 2: 별점 변경 시 export 트리거**

`MainActivity.kt:136-142`의 `adapter` 생성 블록 중 `onRatingChanged` 부분:

```kotlin
            onRatingChanged = { video, rating ->
                VideoPreferenceManager.saveRating(video.path, rating)
            },
```

다음으로 교체:

```kotlin
            onRatingChanged = { video, rating ->
                VideoPreferenceManager.saveRating(video.path, rating)
                RatingBackupManager.scheduleExport()
            },
```

- [ ] **Step 3: 삭제(API 30+ 경로) 시 export 트리거**

`MainActivity.kt:82-94`의 `deleteLauncher`:

```kotlin
    private val deleteLauncher =
        registerForActivityResult(ActivityResultContracts.StartIntentSenderForResult()) { result ->
            if (result.resultCode == Activity.RESULT_OK) {
                pendingDeleteItem?.let { item ->
                    allVideoList.remove(item)
                    VideoPreferenceManager.deleteRating(item.path)
                    adapter.updateList(filterVideos(allVideoList, currentFilter))
                    updateEmptyState()
                    Toast.makeText(this, "파일이 삭제되었습니다.", Toast.LENGTH_SHORT).show()
                }
            }
            pendingDeleteItem = null
        }
```

다음으로 교체 (`RatingBackupManager.scheduleExport()` 한 줄 추가):

```kotlin
    private val deleteLauncher =
        registerForActivityResult(ActivityResultContracts.StartIntentSenderForResult()) { result ->
            if (result.resultCode == Activity.RESULT_OK) {
                pendingDeleteItem?.let { item ->
                    allVideoList.remove(item)
                    VideoPreferenceManager.deleteRating(item.path)
                    RatingBackupManager.scheduleExport()
                    adapter.updateList(filterVideos(allVideoList, currentFilter))
                    updateEmptyState()
                    Toast.makeText(this, "파일이 삭제되었습니다.", Toast.LENGTH_SHORT).show()
                }
            }
            pendingDeleteItem = null
        }
```

- [ ] **Step 4: 삭제(API 29- 레거시 경로) 시 export 트리거**

`MainActivity.kt:282-292`의 `performDelete` 내부:

```kotlin
            val file = File(item.path)
            if (file.delete()) {
                try { contentResolver.delete(uri, null, null) } catch (_: Exception) {}
                allVideoList.remove(item)
                VideoPreferenceManager.deleteRating(item.path)
                adapter.updateList(filterVideos(allVideoList, currentFilter))
                updateEmptyState()
                Toast.makeText(this, "파일이 삭제되었습니다.", Toast.LENGTH_SHORT).show()
            } else {
                Toast.makeText(this, "파일 삭제에 실패했습니다.", Toast.LENGTH_SHORT).show()
            }
```

다음으로 교체:

```kotlin
            val file = File(item.path)
            if (file.delete()) {
                try { contentResolver.delete(uri, null, null) } catch (_: Exception) {}
                allVideoList.remove(item)
                VideoPreferenceManager.deleteRating(item.path)
                RatingBackupManager.scheduleExport()
                adapter.updateList(filterVideos(allVideoList, currentFilter))
                updateEmptyState()
                Toast.makeText(this, "파일이 삭제되었습니다.", Toast.LENGTH_SHORT).show()
            } else {
                Toast.makeText(this, "파일 삭제에 실패했습니다.", Toast.LENGTH_SHORT).show()
            }
```

- [ ] **Step 5: 기본 플레이어 자동 초기화(재생 실패 시) 시 export 트리거**

`MainActivity.kt:316-321`의 `launchWithPackage` 내부 `else` 분기:

```kotlin
            } else {
                VideoPreferenceManager.clearDefaultPlayer()
                Toast.makeText(this, "기본 플레이어를 찾을 수 없습니다. 다시 선택해 주세요.", Toast.LENGTH_SHORT).show()
                showPlayerSelectionDialog(video)
            }
```

다음으로 교체:

```kotlin
            } else {
                VideoPreferenceManager.clearDefaultPlayer()
                RatingBackupManager.scheduleExport()
                Toast.makeText(this, "기본 플레이어를 찾을 수 없습니다. 다시 선택해 주세요.", Toast.LENGTH_SHORT).show()
                showPlayerSelectionDialog(video)
            }
```

- [ ] **Step 6: 기본 플레이어 선택 시 export 트리거**

`MainActivity.kt:340-352`의 `showPlayerSelectionDialog` 내부:

```kotlin
            .setItems(appNames) { _, index ->
                val selected    = players[index]
                val pkgName     = selected.activityInfo.packageName
                val displayName = selected.loadLabel(packageManager).toString()

                VideoPreferenceManager.saveDefaultPlayer(pkgName, displayName)
                Toast.makeText(this, "「$displayName」을(를) 기본 플레이어로 설정했습니다.", Toast.LENGTH_SHORT).show()

                video?.let { launchWithPackage(it, pkgName) }
            }
```

다음으로 교체:

```kotlin
            .setItems(appNames) { _, index ->
                val selected    = players[index]
                val pkgName     = selected.activityInfo.packageName
                val displayName = selected.loadLabel(packageManager).toString()

                VideoPreferenceManager.saveDefaultPlayer(pkgName, displayName)
                RatingBackupManager.scheduleExport()
                Toast.makeText(this, "「$displayName」을(를) 기본 플레이어로 설정했습니다.", Toast.LENGTH_SHORT).show()

                video?.let { launchWithPackage(it, pkgName) }
            }
```

- [ ] **Step 7: 기본 플레이어 초기화(설정 메뉴) 시 export 트리거**

`MainActivity.kt:363-371`의 `showPlayerSettingMenu` 내부:

```kotlin
            .setItems(options) { _, index ->
                when (index) {
                    0 -> showPlayerSelectionDialog(video = null)
                    1 -> {
                        VideoPreferenceManager.clearDefaultPlayer()
                        Toast.makeText(this, "기본 플레이어 설정이 초기화되었습니다.", Toast.LENGTH_SHORT).show()
                    }
                }
            }
```

다음으로 교체:

```kotlin
            .setItems(options) { _, index ->
                when (index) {
                    0 -> showPlayerSelectionDialog(video = null)
                    1 -> {
                        VideoPreferenceManager.clearDefaultPlayer()
                        RatingBackupManager.scheduleExport()
                        Toast.makeText(this, "기본 플레이어 설정이 초기화되었습니다.", Toast.LENGTH_SHORT).show()
                    }
                }
            }
```

- [ ] **Step 8: 빌드 확인**

Run: `./gradlew :app:compileDebugKotlin`
Expected: BUILD SUCCESSFUL

- [ ] **Step 9: 단위 테스트 전체 재확인 (회귀 없음 확인)**

Run: `./gradlew testDebugUnitTest`
Expected: PASS (`VideoFilterTest`, `RatingBackupSerializationTest` 모두 통과)

- [ ] **Step 10: 커밋**

```bash
git add app/src/main/java/com/example/videomanager/MainActivity.kt
git commit -m "feat: trigger rating backup export/restore from MainActivity"
```

(git 저장소가 아니므로 실제 커밋은 생략 가능)

---

### Task 4: 수동 QA (실기기/에뮬레이터)

**Files:** 없음 (수동 검증)

- [ ] **Step 1: 앱 설치 후 별점 부여 → 백업 파일 생성 확인**

앱 실행 → 영상 1개에 별점 부여 → 기기의 파일 관리자(또는 `adb shell ls /sdcard/Download/VideoManager/`)에서 `video_ratings_backup.json` 존재 확인.

Run: `adb shell cat /sdcard/Download/VideoManager/video_ratings_backup.json`
Expected: `ratings`에 방금 매긴 별점이 포함된 JSON 출력

- [ ] **Step 2: 앱 데이터 삭제 후 복원 확인**

Run: `adb shell pm clear com.example.videomanager`

앱 재실행 → "이전 데이터를 백업에서 복원했습니다" Toast 확인 → 이전에 매긴 별점이 그대로 표시되는지 확인.

- [ ] **Step 3: 최초 설치 상태(백업 파일 없음) 정상 동작 확인**

Run: `adb shell rm -rf /sdcard/Download/VideoManager && adb shell pm clear com.example.videomanager`

앱 실행 → 크래시 없이 정상적으로 영상 목록이 로딩되는지 확인 (Toast 없어야 함).

- [ ] **Step 4: 로컬에 데이터가 있을 때 백업으로 덮어써지지 않는지 확인**

별점을 매긴 상태에서 앱을 완전히 종료 후 재실행 → 별점이 백업 파일 내용으로 초기화되지 않고 그대로 유지되는지 확인 (merge 안 함 정책 검증).

- [ ] **Step 5: API 28 이하 에뮬레이터에서 권한 미승인 시 정상 동작 확인**

API 28 이하 AVD 생성 → 앱 설치 후 `WRITE_EXTERNAL_STORAGE` 권한을 거부한 상태로 별점 부여 → 앱이 크래시하지 않고 정상 동작하는지 확인 (백업만 조용히 스킵).
