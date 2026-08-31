# 평점 필터 칩 + 롱클릭 메뉴 + 파일 삭제 구현 계획

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 평점 필터 칩(상단), 롱클릭 액션 메뉴(평점/삭제), 파일 직접 삭제 기능을 VideoManager 앱에 추가한다.

**Architecture:** `VideoFilter.kt`에 순수 필터 로직을 분리하여 단위 테스트 가능하게 만든다. `VideoAdapter`에 삭제 콜백을 추가하고, `MainActivity`가 필터 상태(`allVideoList` + `currentFilter`)와 API별 삭제 처리를 담당한다.

**Tech Stack:** Kotlin, Material Components 1.12.0 (Chip/ChipGroup), MediaStore, ActivityResultContracts

## Global Constraints

- minSdk 21, targetSdk 34, compileSdk 34
- 패키지: `com.example.videomanager`
- Material Components: `1.12.0` (ChipGroup `singleSelection` + `selectionRequired` 지원)
- `WRITE_EXTERNAL_STORAGE` 권한은 `maxSdkVersion="28"`만 선언 (API 29+는 불필요)
- API 29(`Q`) 전용 코드는 `@RequiresApi(Q)` 함수로 분리

---

## 파일 구조

| 파일 | 변경 종류 | 역할 |
|------|---------|------|
| `AndroidManifest.xml` | 수정 | WRITE_EXTERNAL_STORAGE 권한 추가 |
| `res/layout/activity_main.xml` | 수정 | ChipGroup 추가 |
| `VideoFilter.kt` | **신규** | 필터 로직 (순수 함수, 테스트 가능) |
| `VideoAdapter.kt` | 수정 | `onDeleteItem` 콜백 + `showActionMenu()` |
| `MainActivity.kt` | 수정 | allVideoList, 필터 칩, 파일 삭제 |
| `VideoFilterTest.kt` | **신규** | VideoFilter 단위 테스트 |

---

### Task 1: Manifest + Layout 설정

**Files:**
- Modify: `app/src/main/AndroidManifest.xml`
- Modify: `app/src/main/res/layout/activity_main.xml`

**Interfaces:**
- Produces: `@id/chip_group_filter`, `@id/chip_all`, `@id/chip_rating5`, `@id/chip_rating4`, `@id/chip_rating3`, `@id/chip_rating2`, `@id/chip_rating1`, `@id/chip_unrated`

- [ ] **Step 1: AndroidManifest.xml에 WRITE_EXTERNAL_STORAGE 권한 추가**

`READ_MEDIA_VIDEO` `<uses-permission>` 태그 아래에 삽입:

```xml
<uses-permission
    android:name="android.permission.WRITE_EXTERNAL_STORAGE"
    android:maxSdkVersion="28" />
```

- [ ] **Step 2: activity_main.xml 루트 태그에 app 네임스페이스 추가**

`<LinearLayout` 여는 태그에 추가:

```xml
xmlns:app="http://schemas.android.com/apk/res-auto"
```

- [ ] **Step 3: 툴바 `</LinearLayout>` 닫는 태그 직후에 ChipGroup 삽입**

```xml
<!-- ── 평점 필터 칩 ─────────────────────────────────────────── -->
<HorizontalScrollView
    android:layout_width="match_parent"
    android:layout_height="wrap_content"
    android:scrollbars="none"
    android:background="#FFFFFF"
    android:elevation="2dp">

    <com.google.android.material.chip.ChipGroup
        android:id="@+id/chip_group_filter"
        android:layout_width="wrap_content"
        android:layout_height="wrap_content"
        android:paddingStart="12dp"
        android:paddingEnd="12dp"
        android:paddingTop="6dp"
        android:paddingBottom="6dp"
        app:singleSelection="true"
        app:selectionRequired="true">

        <com.google.android.material.chip.Chip
            android:id="@+id/chip_all"
            style="@style/Widget.Material3.Chip.Filter"
            android:layout_width="wrap_content"
            android:layout_height="wrap_content"
            android:text="전체"
            android:checked="true" />

        <com.google.android.material.chip.Chip
            android:id="@+id/chip_rating5"
            style="@style/Widget.Material3.Chip.Filter"
            android:layout_width="wrap_content"
            android:layout_height="wrap_content"
            android:text="★5" />

        <com.google.android.material.chip.Chip
            android:id="@+id/chip_rating4"
            style="@style/Widget.Material3.Chip.Filter"
            android:layout_width="wrap_content"
            android:layout_height="wrap_content"
            android:text="★4" />

        <com.google.android.material.chip.Chip
            android:id="@+id/chip_rating3"
            style="@style/Widget.Material3.Chip.Filter"
            android:layout_width="wrap_content"
            android:layout_height="wrap_content"
            android:text="★3" />

        <com.google.android.material.chip.Chip
            android:id="@+id/chip_rating2"
            style="@style/Widget.Material3.Chip.Filter"
            android:layout_width="wrap_content"
            android:layout_height="wrap_content"
            android:text="★2" />

        <com.google.android.material.chip.Chip
            android:id="@+id/chip_rating1"
            style="@style/Widget.Material3.Chip.Filter"
            android:layout_width="wrap_content"
            android:layout_height="wrap_content"
            android:text="★1" />

        <com.google.android.material.chip.Chip
            android:id="@+id/chip_unrated"
            style="@style/Widget.Material3.Chip.Filter"
            android:layout_width="wrap_content"
            android:layout_height="wrap_content"
            android:text="미평가" />

    </com.google.android.material.chip.ChipGroup>
</HorizontalScrollView>
```

- [ ] **Step 4: 레이아웃 XML 컴파일 확인**

```bash
cd /Users/kys1207/AndroidStudioProjects/TestFileView
./gradlew :app:processDebugResources --no-daemon 2>&1 | grep -E "error:|ERROR" | head -10
```

Expected: 출력 없음

- [ ] **Step 5: 커밋**

```bash
git add app/src/main/AndroidManifest.xml app/src/main/res/layout/activity_main.xml
git commit -m "feat: add rating filter chipgroup and write permission declaration"
```

---

### Task 2: VideoFilter.kt 신규 생성 + VideoAdapter.kt 수정

**Files:**
- Create: `app/src/main/java/com/example/videomanager/VideoFilter.kt`
- Create: `app/src/test/java/com/example/videomanager/VideoFilterTest.kt`
- Modify: `app/src/main/java/com/example/videomanager/VideoAdapter.kt`

**Interfaces:**
- Produces:
  - `sealed class RatingFilter { object ALL; object UNRATED; data class Stars(val stars: Int) }`
  - `fun filterVideos(videos: List<VideoItem>, filter: RatingFilter): List<VideoItem>`
  - `VideoAdapter` 생성자에 `onDeleteItem: (VideoItem) -> Unit` 파라미터 추가

- [ ] **Step 1: 테스트 파일 먼저 작성**

경로: `app/src/test/java/com/example/videomanager/VideoFilterTest.kt`

```kotlin
package com.example.videomanager

import org.junit.Assert.assertEquals
import org.junit.Test

class VideoFilterTest {

    private fun item(path: String, rating: Float) =
        VideoItem(id = 0, name = path, path = path, duration = 0, size = 0, dateModified = 0, rating = rating)

    private val videos = listOf(
        item("a", 5f),
        item("b", 4.5f),
        item("c", 4.0f),
        item("d", 3.0f),
        item("e", 2.0f),
        item("f", 1.0f),
        item("g", 0f),
        item("h", 0f)
    )

    @Test fun `ALL returns all videos`() {
        assertEquals(8, filterVideos(videos, RatingFilter.ALL).size)
    }

    @Test fun `Stars 5 returns only rating exactly 5`() {
        val result = filterVideos(videos, RatingFilter.Stars(5))
        assertEquals(1, result.size)
        assertEquals("a", result[0].path)
    }

    @Test fun `Stars 4 returns rating 4_0 to 4_9`() {
        val result = filterVideos(videos, RatingFilter.Stars(4))
        assertEquals(2, result.size) // b(4.5), c(4.0)
    }

    @Test fun `Stars 1 returns rating 1_0 to 1_9`() {
        val result = filterVideos(videos, RatingFilter.Stars(1))
        assertEquals(1, result.size)
        assertEquals("f", result[0].path)
    }

    @Test fun `UNRATED returns rating 0`() {
        val result = filterVideos(videos, RatingFilter.UNRATED)
        assertEquals(2, result.size) // g, h
    }

    @Test fun `empty input always returns empty`() {
        assertEquals(0, filterVideos(emptyList(), RatingFilter.Stars(3)).size)
        assertEquals(0, filterVideos(emptyList(), RatingFilter.UNRATED).size)
        assertEquals(0, filterVideos(emptyList(), RatingFilter.ALL).size)
    }
}
```

- [ ] **Step 2: 테스트 실패 확인**

```bash
./gradlew :app:testDebugUnitTest --tests "com.example.videomanager.VideoFilterTest" --no-daemon 2>&1 | tail -8
```

Expected: `BUILD FAILED` — `filterVideos` 미구현 컴파일 에러

- [ ] **Step 3: VideoFilter.kt 구현**

경로: `app/src/main/java/com/example/videomanager/VideoFilter.kt`

```kotlin
package com.example.videomanager

sealed class RatingFilter {
    object ALL : RatingFilter()
    object UNRATED : RatingFilter()
    data class Stars(val stars: Int) : RatingFilter()
}

fun filterVideos(videos: List<VideoItem>, filter: RatingFilter): List<VideoItem> =
    when (filter) {
        RatingFilter.ALL     -> videos
        RatingFilter.UNRATED -> videos.filter { it.rating == 0f }
        is RatingFilter.Stars -> videos.filter {
            if (filter.stars == 5) it.rating == 5f
            else it.rating >= filter.stars.toFloat() && it.rating < (filter.stars + 1).toFloat()
        }
    }
```

- [ ] **Step 4: 테스트 통과 확인**

```bash
./gradlew :app:testDebugUnitTest --tests "com.example.videomanager.VideoFilterTest" --no-daemon 2>&1 | tail -5
```

Expected: `BUILD SUCCESSFUL`

- [ ] **Step 5: VideoAdapter.kt — 생성자에 `onDeleteItem` 추가**

`class VideoAdapter(` 선언부를 아래로 교체:

```kotlin
class VideoAdapter(
    private val context: Context,
    private val videoList: MutableList<VideoItem>,
    private val onItemClick: (VideoItem) -> Unit,
    private val onRatingChanged: (VideoItem, Float) -> Unit,
    private val onDeleteItem: (VideoItem) -> Unit
) : RecyclerView.Adapter<VideoAdapter.VideoViewHolder>() {
```

- [ ] **Step 6: VideoAdapter.kt — `bindClickListeners` 롱클릭을 `showActionMenu`로 변경**

기존:
```kotlin
private fun bindClickListeners(holder: VideoViewHolder, item: VideoItem) {
    holder.itemView.setOnClickListener { onItemClick(item) }
    holder.itemView.setOnLongClickListener {
        showRatingDialog(item, holder.adapterPosition)
        true
    }
}
```

교체:
```kotlin
private fun bindClickListeners(holder: VideoViewHolder, item: VideoItem) {
    holder.itemView.setOnClickListener { onItemClick(item) }
    holder.itemView.setOnLongClickListener {
        showActionMenu(item, holder.adapterPosition)
        true
    }
}
```

- [ ] **Step 7: VideoAdapter.kt — `showActionMenu` 메서드 추가**

`showRatingDialog()` 메서드 바로 위에 삽입:

```kotlin
private fun showActionMenu(item: VideoItem, position: Int) {
    val options = arrayOf("★ 평점 주기", "🗑 파일 삭제")
    MaterialAlertDialogBuilder(context)
        .setTitle(item.name)
        .setItems(options) { _, index ->
            when (index) {
                0 -> showRatingDialog(item, position)
                1 -> onDeleteItem(item)
            }
        }
        .setNegativeButton("취소", null)
        .show()
}
```

- [ ] **Step 8: 컴파일 확인 (MainActivity 생성자 불일치 에러 예상 — Task 3에서 수정)**

```bash
./gradlew :app:compileDebugKotlin --no-daemon 2>&1 | grep "^e: " | head -10
```

Expected: `MainActivity.kt`에서 VideoAdapter 생성자 인자 부족 에러 1건 (정상)

- [ ] **Step 9: 커밋**

```bash
git add app/src/main/java/com/example/videomanager/VideoFilter.kt \
        app/src/main/java/com/example/videomanager/VideoAdapter.kt \
        app/src/test/java/com/example/videomanager/VideoFilterTest.kt
git commit -m "feat: add VideoFilter logic and adapter action menu with delete callback"
```

---

### Task 3: MainActivity.kt — 필터 칩 연결 + 파일 삭제 처리

**Files:**
- Modify: `app/src/main/java/com/example/videomanager/MainActivity.kt`

**Interfaces:**
- Consumes:
  - `filterVideos(videos: List<VideoItem>, filter: RatingFilter): List<VideoItem>`
  - `RatingFilter.ALL`, `RatingFilter.UNRATED`, `RatingFilter.Stars(stars: Int)`
  - `VideoAdapter(..., onDeleteItem: (VideoItem) -> Unit)`

- [ ] **Step 1: import 추가**

기존 import 블록 맨 아래에 추가:

```kotlin
import android.annotation.SuppressLint
import android.app.Activity
import android.content.ContentUris
import android.os.Build
import android.os.RecoverableSecurityException
import androidx.activity.result.IntentSenderRequest
import androidx.activity.result.contract.ActivityResultContracts
import com.google.android.material.chip.ChipGroup
```

- [ ] **Step 2: 클래스 필드 추가**

`// --- Data & Adapter` 섹션의 `private val videoList` 바로 아래에 삽입:

```kotlin
private val allVideoList = mutableListOf<VideoItem>()
private var currentFilter: RatingFilter = RatingFilter.ALL
private var pendingDeleteItem: VideoItem? = null
private lateinit var chipGroupFilter: ChipGroup
```

- [ ] **Step 3: ActivityResultLauncher 2개 추가**

기존 `permissionLauncher` 선언 바로 아래에 삽입:

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

private val writePermLauncher =
    registerForActivityResult(ActivityResultContracts.RequestPermission()) { granted ->
        if (granted) {
            pendingDeleteItem?.let { performDelete(it) }
        } else {
            Toast.makeText(this, "파일 삭제에 쓰기 권한이 필요합니다.", Toast.LENGTH_SHORT).show()
            pendingDeleteItem = null
        }
    }
```

- [ ] **Step 4: `initViews()`에 ChipGroup 연결 + adapter에 `onDeleteItem` 추가**

`initViews()` 내 `progressBar = ...` 줄들 아래에 `chipGroupFilter` 초기화 추가:

```kotlin
chipGroupFilter = findViewById(R.id.chip_group_filter)
```

기존 `adapter = VideoAdapter(...)` 블록을 아래로 교체:

```kotlin
adapter = VideoAdapter(
    context         = this,
    videoList       = videoList,
    onItemClick     = { video -> openVideoPlayer(video) },
    onRatingChanged = { video, rating ->
        VideoPreferenceManager.saveRating(video.path, rating)
    },
    onDeleteItem    = { video -> confirmAndDelete(video) }
)
```

`initViews()` 맨 끝(기존 `btnPlayerSetting.setOnClickListener` 아래)에 칩 리스너 추가:

```kotlin
chipGroupFilter.setOnCheckedStateChangeListener { _, checkedIds ->
    currentFilter = when (checkedIds.firstOrNull()) {
        R.id.chip_rating5  -> RatingFilter.Stars(5)
        R.id.chip_rating4  -> RatingFilter.Stars(4)
        R.id.chip_rating3  -> RatingFilter.Stars(3)
        R.id.chip_rating2  -> RatingFilter.Stars(2)
        R.id.chip_rating1  -> RatingFilter.Stars(1)
        R.id.chip_unrated  -> RatingFilter.UNRATED
        else               -> RatingFilter.ALL
    }
    adapter.updateList(filterVideos(allVideoList, currentFilter))
    updateEmptyState()
}
```

- [ ] **Step 5: `loadVideos()` 수정 — allVideoList 갱신 + 필터 초기화**

기존 `loadVideos()` 전체를 교체:

```kotlin
private fun loadVideos() {
    scope.launch {
        showLoading(true)
        val result = withContext(Dispatchers.IO) { queryVideosFromMediaStore() }
        allVideoList.clear()
        allVideoList.addAll(result)
        allVideoList.shuffle()
        currentFilter = RatingFilter.ALL
        chipGroupFilter.check(R.id.chip_all)
        videoList.clear()
        videoList.addAll(allVideoList)
        adapter.notifyDataSetChanged()
        showLoading(false)
        updateEmptyState()
    }
}
```

기존 `btnShuffle.setOnClickListener` 블록을 교체:

```kotlin
btnShuffle.setOnClickListener {
    if (allVideoList.isNotEmpty()) {
        allVideoList.shuffle()
        adapter.updateList(filterVideos(allVideoList, currentFilter))
    }
}
```

- [ ] **Step 6: `confirmAndDelete` + `performDelete` + `deleteOnApi29` 추가**

`openVideoPlayer()` 메서드 바로 위에 삽입:

```kotlin
private fun confirmAndDelete(item: VideoItem) {
    MaterialAlertDialogBuilder(this)
        .setTitle("파일 삭제")
        .setMessage("「${item.name}」을 삭제하시겠습니까?\n이 작업은 되돌릴 수 없습니다.")
        .setPositiveButton("삭제") { _, _ -> performDelete(item) }
        .setNegativeButton("취소", null)
        .show()
}

private fun performDelete(item: VideoItem) {
    val uri = ContentUris.withAppendedId(
        MediaStore.Video.Media.EXTERNAL_CONTENT_URI, item.id
    )
    when {
        Build.VERSION.SDK_INT >= Build.VERSION_CODES.R -> {
            val request = MediaStore.createDeleteRequest(contentResolver, listOf(uri))
            pendingDeleteItem = item
            deleteLauncher.launch(
                IntentSenderRequest.Builder(request.intentSender).build()
            )
        }
        Build.VERSION.SDK_INT == Build.VERSION_CODES.Q -> {
            deleteOnApi29(item, uri)
        }
        else -> {
            if (ContextCompat.checkSelfPermission(
                    this, Manifest.permission.WRITE_EXTERNAL_STORAGE
                ) != PackageManager.PERMISSION_GRANTED
            ) {
                pendingDeleteItem = item
                writePermLauncher.launch(Manifest.permission.WRITE_EXTERNAL_STORAGE)
                return
            }
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
        }
    }
}

@SuppressLint("NewApi")
@androidx.annotation.RequiresApi(Build.VERSION_CODES.Q)
private fun deleteOnApi29(item: VideoItem, uri: android.net.Uri) {
    try {
        contentResolver.delete(uri, null, null)
        allVideoList.remove(item)
        VideoPreferenceManager.deleteRating(item.path)
        adapter.updateList(filterVideos(allVideoList, currentFilter))
        updateEmptyState()
        Toast.makeText(this, "파일이 삭제되었습니다.", Toast.LENGTH_SHORT).show()
    } catch (e: RecoverableSecurityException) {
        pendingDeleteItem = item
        deleteLauncher.launch(
            IntentSenderRequest.Builder(e.userAction.actionIntent.intentSender).build()
        )
    }
}
```

- [ ] **Step 7: 전체 빌드 확인**

```bash
./gradlew :app:assembleDebug --no-daemon 2>&1 | grep -E "^(BUILD|> Task :.*FAILED|e: )" | tail -20
```

Expected: `BUILD SUCCESSFUL`

- [ ] **Step 8: 단위 테스트 최종 확인**

```bash
./gradlew :app:testDebugUnitTest --no-daemon 2>&1 | tail -5
```

Expected: `BUILD SUCCESSFUL`

- [ ] **Step 9: 커밋**

```bash
git add app/src/main/java/com/example/videomanager/MainActivity.kt
git commit -m "feat: wire rating filter chips and file delete in MainActivity"
```
