# Firebase Remote Config 강제 업데이트 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 앱 실행 시 Firebase Remote Config로 최소 지원 버전을 확인해, 구버전이면 생체/PIN 인증 이전에 강제로 업데이트 다이얼로그로 막는다.

**Architecture:** Firebase SDK 호출부(`ForceUpdateGate`)와 버전 비교 판단 로직(`ForceUpdatePolicy`, 순수 함수)을 분리한다. `MainActivity.onCreate()`가 인증 시도 전에 게이트를 먼저 통과시킨다.

**Tech Stack:** Kotlin, Firebase Remote Config (`com.google.firebase:firebase-config`), 기존 코루틴 패턴(`suspendCancellableCoroutine`, `CoroutineScope`).

**Spec:** `docs/superpowers/specs/2026-08-31-firebase-remote-config-force-update-design.md`

## Global Constraints

- 이 프로젝트(`/Users/kys1207/AndroidStudioProjects/VideoManager`)는 git 저장소가 아니다. **어떤 태스크에서도 git 명령을 실행하지 않는다.** 각 태스크의 "커밋" 단계는 생략한다 — 전체 계획이 끝난 뒤 조율 세션이 한 번에 별도 미러 저장소에 반영한다.
- Firebase BOM 버전은 `33.5.1`로 고정한다. `compileDebugKotlin` 실행 시 의존성 해석에 실패하면(더 이상 존재하지 않는 버전이면) https://firebase.google.com/support/release-notes/android 에서 최신 33.x/34.x 버전을 확인해 교체한다.
- Remote Config 조회가 실패(네트워크 없음/타임아웃/예외)하면 항상 `ForceUpdateDecision.ALLOW`로 처리한다(fail-open) — 절대 앱을 막지 않는다.
- 버전 비교는 정수 `versionCode`만 사용한다. `versionName` 문자열 파싱은 하지 않는다.
- 강제 업데이트 검사는 `authenticateBeforeOpening()`(생체/PIN 인증) 호출보다 반드시 먼저 실행한다.
- 새 패키지 `com.kys.videomanager.update` 아래에 만든다 (`app/src/main/java/com/kys/videomanager/update/`, 테스트는 `app/src/test/java/com/kys/videomanager/update/`).

---

### Task 1: ForceUpdatePolicy 순수 로직 (TDD)

**Files:**
- Create: `app/src/test/java/com/kys/videomanager/update/ForceUpdatePolicyTest.kt`
- Create: `app/src/main/java/com/kys/videomanager/update/ForceUpdatePolicy.kt`

**Interfaces:**
- Produces: `enum class ForceUpdateDecision { ALLOW, BLOCK }`, `object ForceUpdatePolicy { fun resolve(currentVersionCode: Int, minSupportedVersionCode: Long): ForceUpdateDecision }`

- [ ] **Step 1: Write the failing test**

```kotlin
package com.kys.videomanager.update

import org.junit.Assert.assertEquals
import org.junit.Test

class ForceUpdatePolicyTest {

    @Test
    fun `current version equal to minimum allows`() {
        assertEquals(
            ForceUpdateDecision.ALLOW,
            ForceUpdatePolicy.resolve(currentVersionCode = 6, minSupportedVersionCode = 6L)
        )
    }

    @Test
    fun `current version greater than minimum allows`() {
        assertEquals(
            ForceUpdateDecision.ALLOW,
            ForceUpdatePolicy.resolve(currentVersionCode = 7, minSupportedVersionCode = 6L)
        )
    }

    @Test
    fun `current version less than minimum blocks`() {
        assertEquals(
            ForceUpdateDecision.BLOCK,
            ForceUpdatePolicy.resolve(currentVersionCode = 5, minSupportedVersionCode = 6L)
        )
    }

    @Test
    fun `default minimum of zero always allows`() {
        assertEquals(
            ForceUpdateDecision.ALLOW,
            ForceUpdatePolicy.resolve(currentVersionCode = 1, minSupportedVersionCode = 0L)
        )
    }
}
```

- [ ] **Step 2: Run test to verify it fails**

Run: `./gradlew :app:testDebugUnitTest --tests "com.kys.videomanager.update.ForceUpdatePolicyTest" --console=plain`
Expected: FAIL — compile error, `ForceUpdateDecision`/`ForceUpdatePolicy` unresolved references.

- [ ] **Step 3: Write minimal implementation**

```kotlin
package com.kys.videomanager.update

enum class ForceUpdateDecision {
    ALLOW,
    BLOCK
}

object ForceUpdatePolicy {
    fun resolve(currentVersionCode: Int, minSupportedVersionCode: Long): ForceUpdateDecision =
        if (currentVersionCode < minSupportedVersionCode) {
            ForceUpdateDecision.BLOCK
        } else {
            ForceUpdateDecision.ALLOW
        }
}
```

- [ ] **Step 4: Run test to verify it passes**

Run: `./gradlew :app:testDebugUnitTest --tests "com.kys.videomanager.update.ForceUpdatePolicyTest" --console=plain`
Expected: PASS, 4 tests, 0 failures.

- [ ] **Step 5: Mark task complete**

No git commit (see Global Constraints). Proceed to Task 2.

---

### Task 2: Firebase Remote Config 의존성 + ForceUpdateGate

**Files:**
- Modify: `app/build.gradle` (add `buildFeatures.buildConfig` if missing, add Firebase BOM + `firebase-config` dependency)
- Create: `app/src/main/java/com/kys/videomanager/update/ForceUpdateGate.kt`

**Interfaces:**
- Consumes: `ForceUpdateDecision`, `ForceUpdatePolicy.resolve(currentVersionCode: Int, minSupportedVersionCode: Long): ForceUpdateDecision` (Task 1)
- Produces: `data class ForceUpdateResult(val decision: ForceUpdateDecision, val updateUrl: String, val message: String)`, `class ForceUpdateGate(context: Context) { suspend fun check(currentVersionCode: Int): ForceUpdateResult }`

- [ ] **Step 1: Check whether BuildConfig generation is enabled**

Read `app/build.gradle` (`android { ... }` block) and `gradle.properties`. If `gradle.properties` does not contain `android.defaults.buildfeatures.buildconfig=true` and `app/build.gradle`'s `android { }` block has no `buildFeatures { buildConfig true }`, add this block inside `android { }` in `app/build.gradle`, immediately after the existing `kotlinOptions { jvmTarget = "17" }` block:

```groovy
    buildFeatures {
        buildConfig true
    }
```

(MainActivity needs `BuildConfig.VERSION_CODE` in Task 3 — without this the generated `BuildConfig` class won't exist.)

- [ ] **Step 2: Add Firebase Remote Config dependency**

In `app/build.gradle`, inside the `dependencies { }` block, add these two lines near the top (before the existing `androidx.core.ktx` line):

```groovy
    implementation platform('com.google.firebase:firebase-bom:33.5.1')
    implementation 'com.google.firebase:firebase-config'
```

- [ ] **Step 3: Verify the dependency resolves**

Run: `./gradlew :app:compileDebugKotlin --console=plain`
Expected: `BUILD SUCCESSFUL`. If it fails with a message that `firebase-bom:33.5.1` cannot be found, check https://firebase.google.com/support/release-notes/android for the latest `33.x`/`34.x` BOM version, replace `33.5.1` with it, and re-run this step.

- [ ] **Step 4: Write ForceUpdateGate**

Create `app/src/main/java/com/kys/videomanager/update/ForceUpdateGate.kt`:

```kotlin
package com.kys.videomanager.update

import android.content.Context
import com.google.android.gms.tasks.Task
import com.google.firebase.remoteconfig.FirebaseRemoteConfig
import com.google.firebase.remoteconfig.FirebaseRemoteConfigSettings
import kotlinx.coroutines.suspendCancellableCoroutine

data class ForceUpdateResult(
    val decision: ForceUpdateDecision,
    val updateUrl: String,
    val message: String
)

/**
 * Firebase Remote Config를 조회해 강제 업데이트 여부를 판단한다.
 * 조회가 어떤 이유로든 실패하면 항상 ALLOW를 반환한다(fail-open) —
 * Firebase 장애나 오프라인 상태로 앱 자체가 막히는 일이 없어야 한다.
 */
class ForceUpdateGate(private val context: Context) {

    private val defaultUpdateUrl: String
        get() = "https://play.google.com/store/apps/details?id=${context.packageName}"

    suspend fun check(currentVersionCode: Int): ForceUpdateResult {
        return try {
            val remoteConfig = FirebaseRemoteConfig.getInstance()
            remoteConfig.setConfigSettingsAsync(
                FirebaseRemoteConfigSettings.Builder()
                    .setMinimumFetchIntervalInSeconds(MIN_FETCH_INTERVAL_SECONDS)
                    .build()
            ).await()
            remoteConfig.setDefaultsAsync(
                mapOf(
                    KEY_MIN_SUPPORTED_VERSION_CODE to currentVersionCode.toLong(),
                    KEY_UPDATE_URL to defaultUpdateUrl,
                    KEY_UPDATE_MESSAGE to DEFAULT_UPDATE_MESSAGE
                )
            ).await()
            remoteConfig.fetchAndActivate().await()

            val minSupportedVersionCode = remoteConfig.getLong(KEY_MIN_SUPPORTED_VERSION_CODE)
            val updateUrl = remoteConfig.getString(KEY_UPDATE_URL).ifBlank { defaultUpdateUrl }
            val message = remoteConfig.getString(KEY_UPDATE_MESSAGE).ifBlank { DEFAULT_UPDATE_MESSAGE }

            ForceUpdateResult(
                decision = ForceUpdatePolicy.resolve(currentVersionCode, minSupportedVersionCode),
                updateUrl = updateUrl,
                message = message
            )
        } catch (e: Exception) {
            ForceUpdateResult(
                decision = ForceUpdateDecision.ALLOW,
                updateUrl = defaultUpdateUrl,
                message = DEFAULT_UPDATE_MESSAGE
            )
        }
    }

    private suspend fun <T> Task<T>.await(): T =
        suspendCancellableCoroutine { continuation ->
            addOnCompleteListener { task ->
                if (task.isSuccessful) {
                    continuation.resumeWith(Result.success(task.result))
                } else {
                    continuation.resumeWith(
                        Result.failure(task.exception ?: RuntimeException("Task failed with no exception"))
                    )
                }
            }
        }

    companion object {
        private const val MIN_FETCH_INTERVAL_SECONDS = 3600L
        private const val KEY_MIN_SUPPORTED_VERSION_CODE = "min_supported_version_code"
        private const val KEY_UPDATE_URL = "update_url"
        private const val KEY_UPDATE_MESSAGE = "update_message"
        private const val DEFAULT_UPDATE_MESSAGE = "새 버전이 있습니다. 업데이트 후 이용해 주세요."
    }
}
```

- [ ] **Step 5: Verify it compiles**

Run: `./gradlew :app:compileDebugKotlin --console=plain`
Expected: `BUILD SUCCESSFUL`.

- [ ] **Step 6: Run full unit test suite to confirm no regressions**

Run: `./gradlew :app:testDebugUnitTest --console=plain`
Expected: `BUILD SUCCESSFUL`, same pass count as before this task plus the 4 tests from Task 1 (153 + 4 = 157 total, assuming no other changes landed since the browser-tab work).

- [ ] **Step 7: Mark task complete**

No git commit (see Global Constraints). Proceed to Task 3.

---

### Task 3: MainActivity 연동 (강제 업데이트 차단 다이얼로그)

**Files:**
- Modify: `app/src/main/java/com/kys/videomanager/main/MainActivity.kt`

**Interfaces:**
- Consumes: `ForceUpdateGate(context: Context).check(currentVersionCode: Int): ForceUpdateResult` (Task 2), `ForceUpdateResult(decision, updateUrl, message)` (Task 2), `ForceUpdateDecision.BLOCK`/`ForceUpdateDecision.ALLOW` (Task 1), `com.kys.videomanager.BuildConfig.VERSION_CODE` (generated)

- [ ] **Step 1: Add imports**

In `app/src/main/java/com/kys/videomanager/main/MainActivity.kt`, add these imports near the other `com.kys.videomanager.*` imports at the top of the file (alongside the existing `import com.kys.videomanager.R` line):

```kotlin
import com.kys.videomanager.BuildConfig
import com.kys.videomanager.update.ForceUpdateDecision
import com.kys.videomanager.update.ForceUpdateGate
import com.kys.videomanager.update.ForceUpdateResult
```

- [ ] **Step 2: Replace the onCreate body**

Find the existing `onCreate` method:

```kotlin
    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        authenticateBeforeOpening()
    }
```

Replace it with:

```kotlin
    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        checkForceUpdate()
    }

    private fun checkForceUpdate() {
        scope.launch {
            val result = ForceUpdateGate(this@MainActivity).check(BuildConfig.VERSION_CODE)
            if (result.decision == ForceUpdateDecision.BLOCK) {
                showForceUpdateDialog(result)
            } else {
                authenticateBeforeOpening()
            }
        }
    }

    private fun showForceUpdateDialog(result: ForceUpdateResult) {
        MaterialAlertDialogBuilder(this)
            .setTitle("업데이트 필요")
            .setMessage(result.message)
            .setCancelable(false)
            .setPositiveButton("업데이트") { _, _ ->
                try {
                    startActivity(Intent(Intent.ACTION_VIEW, Uri.parse(result.updateUrl)))
                } catch (e: Exception) {
                    Toast.makeText(
                        this,
                        "스토어를 열 수 없습니다: ${e.message ?: e.javaClass.simpleName}",
                        Toast.LENGTH_SHORT
                    ).show()
                }
                finish()
            }
            .show()
    }
```

(`scope`, `MaterialAlertDialogBuilder`, `Intent`, `Uri`, `Toast` are all already used/imported elsewhere in this file — no further imports needed for this step. `setCancelable(false)` on the dialog means the system back button does nothing while it's showing, so no separate back-press handling is needed to keep the user from bypassing it.)

- [ ] **Step 3: Verify it compiles**

Run: `./gradlew :app:compileDebugKotlin --console=plain`
Expected: `BUILD SUCCESSFUL`.

- [ ] **Step 4: Run full unit test suite**

Run: `./gradlew :app:testDebugUnitTest --console=plain`
Expected: `BUILD SUCCESSFUL`, same test count as after Task 2 (157 tests — this task adds no new unit tests, since Firebase/UI aren't unit-testable per the spec's test strategy).

- [ ] **Step 5: Verify the release APK still assembles**

Run: `./gradlew :app:assembleDebug --console=plain`
Expected: `BUILD SUCCESSFUL`.

- [ ] **Step 6: Manual verification note (no automated test possible)**

Record in the task report that the following must be manually verified on a device once a Firebase Remote Config console value is set (this cannot be automated — same limitation noted in the spec for all Firebase/UI code in this app):
- Setting `min_supported_version_code` in the Firebase console higher than the installed `versionCode` (6) shows the blocking dialog before any biometric/PIN prompt, and the back button does not dismiss it.
- Tapping "업데이트" opens the Play Store page for `com.kys.videomanager` and closes the app.
- With no Remote Config value set (or Remote Config unreachable, e.g. airplane mode), the app proceeds straight to the existing biometric prompt as before.

- [ ] **Step 7: Mark task complete**

No git commit (see Global Constraints). This is the final task in the plan.

---

## Self-Review Notes

- **Spec coverage**: `ForceUpdatePolicy`/`ForceUpdateDecision` (Task 1) ✅, Remote Config keys + fail-open + defaults (Task 2) ✅, ordering before `authenticateBeforeOpening()` + blocking dialog + Play Store link (Task 3) ✅. Firebase BOM dependency addition ✅ (Task 2, Step 1-2). All spec sections have a covering task.
- **Placeholder scan**: no TBD/TODO; all code blocks are complete, runnable Kotlin.
- **Type consistency**: `ForceUpdateDecision` (Task 1) is consumed as-is in `ForceUpdateResult`/`ForceUpdateGate` (Task 2) and in `MainActivity` (Task 3) without renaming. `ForceUpdateGate(context: Context).check(currentVersionCode: Int): ForceUpdateResult` signature is identical everywhere it's referenced.
- **Scope check**: single subsystem (force-update gate), matches the one spec it implements. No decomposition needed.
