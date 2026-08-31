package com.kys.videomanager.update

import android.content.Context
import com.google.android.gms.tasks.Task
import com.google.firebase.remoteconfig.FirebaseRemoteConfig
import com.google.firebase.remoteconfig.FirebaseRemoteConfigSettings
import kotlinx.coroutines.CancellationException
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
                    .setFetchTimeoutInSeconds(FETCH_TIMEOUT_SECONDS)
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
        } catch (e: CancellationException) {
            throw e
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
        private const val FETCH_TIMEOUT_SECONDS = 10L
        private const val KEY_MIN_SUPPORTED_VERSION_CODE = "min_supported_version_code"
        private const val KEY_UPDATE_URL = "update_url"
        private const val KEY_UPDATE_MESSAGE = "update_message"
        private const val DEFAULT_UPDATE_MESSAGE = "새 버전이 있습니다. 업데이트 후 이용해 주세요."
    }
}
