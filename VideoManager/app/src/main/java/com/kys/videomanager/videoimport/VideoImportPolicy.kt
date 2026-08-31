package com.kys.videomanager.videoimport

import java.text.SimpleDateFormat
import java.util.Date
import java.util.Locale
import java.util.TimeZone

data class VideoImportPolicy(
    val shouldCompress: Boolean,
    val targetHeight: Int,
    val targetBitrate: Int,
    val targetFrameRate: Int,
    val option: VideoImportOption
) {
    companion object {
        const val TARGET_FRAME_RATE = 30

        fun evaluate(
            width: Int? = null,
            height: Int?,
            bitrate: Int?,
            option: VideoImportOption = VideoImportOption.compress()
        ): VideoImportPolicy =
            VideoImportPolicy(
                shouldCompress = option.shouldCompress(width, height, bitrate),
                targetHeight = option.outputHeight(width, height),
                targetBitrate = option.videoBitrate,
                targetFrameRate = TARGET_FRAME_RATE,
                option = option
            )
    }
}

data class VideoImportOption(
    val label: String,
    val description: String,
    val targetHeight: Int,
    val videoBitrate: Int
) {
    fun shouldCompress(width: Int?, height: Int?, bitrate: Int?): Boolean {
        val basisHeight = resolutionBasisHeight(width, height)
        if (this == original || basisHeight == null) return false
        return basisHeight > targetHeight || (bitrate != null && bitrate > videoBitrate)
    }

    fun outputHeight(width: Int?, height: Int?): Int =
        if (this == original) targetHeight else minOf(resolutionBasisHeight(width, height) ?: targetHeight, targetHeight)

    private fun resolutionBasisHeight(width: Int?, height: Int?): Int? {
        val knownDimensions = listOfNotNull(width, height).filter { it > 0 }
        return knownDimensions.minOrNull()
    }

    companion object {
        const val TARGET_HEIGHT = 1080
        const val DEFAULT_BITRATE = 1_500_000
        const val MIN_BITRATE = 1_000_000
        const val MAX_BITRATE = 2_000_000

        val original = VideoImportOption(
            label = "원본",
            description = "선택한 영상을 압축하지 않고 그대로 가져옵니다.",
            targetHeight = Int.MAX_VALUE,
            videoBitrate = 0
        )

        fun compress(videoBitrate: Int = DEFAULT_BITRATE): VideoImportOption =
            VideoImportOption(
                label = "압축",
                description = "1080p 초과 또는 선택 Mbps보다 큰 영상만 압축합니다.",
                targetHeight = TARGET_HEIGHT,
                videoBitrate = videoBitrate.coerceIn(MIN_BITRATE, MAX_BITRATE)
            )
    }
}

enum class VideoQualityStatus(
    val label: String,
    val color: Int
) {
    HIGH_QUALITY("고화질", 0xFF3F51B5.toInt()),
    STANDARD("보통", 0xFF00897B.toInt()),
    LIGHTWEIGHT("가벼움", 0xFF43A047.toInt()),
    UNKNOWN("정보 부족", 0xFF757575.toInt());

    companion object {
        fun evaluate(width: Int?, height: Int?, bitrate: Int?): VideoQualityStatus {
            val h = height ?: return UNKNOWN
            val b = bitrate
            return when {
                h > 1080 || (h >= 1080 && b != null && b >= 5_000_000) -> HIGH_QUALITY
                h <= 720 && b != null && b <= 1_200_000 -> LIGHTWEIGHT
                else -> STANDARD
            }
        }
    }
}

data class VideoImportPreview(
    val name: String,
    val width: Int?,
    val height: Int?,
    val bitrate: Int?,
    val sizeBytes: Long?,
    val durationMs: Long?,
    val codecLabel: String,
    val policy: VideoImportPolicy,
    val qualityStatus: VideoQualityStatus
) {
    val actionLabel: String
        get() = if (policy.shouldCompress) "압축됨" else "그대로"

    val actionColor: Int
        get() = if (policy.shouldCompress) 0xFFEF6C00.toInt() else 0xFF2E7D32.toInt()

    val estimatedOutputSizeBytes: Long?
        get() {
            if (!policy.shouldCompress) return sizeBytes
            val duration = durationMs?.takeIf { it > 0L } ?: return null
            val totalBitrate = policy.targetBitrate + ESTIMATED_AUDIO_BITRATE
            return (duration * totalBitrate) / 8_000L
        }

    companion object {
        private const val ESTIMATED_AUDIO_BITRATE = 128_000

        fun create(
            name: String,
            width: Int?,
            height: Int?,
            bitrate: Int?,
            sizeBytes: Long?,
            durationMs: Long? = null,
            codecMime: String? = null,
            option: VideoImportOption
        ): VideoImportPreview =
            VideoImportPreview(
                name = name,
                width = width,
                height = height,
                bitrate = bitrate,
                sizeBytes = sizeBytes,
                durationMs = durationMs,
                codecLabel = VideoCodecName.fromMime(codecMime),
                policy = VideoImportPolicy.evaluate(width = width, height = height, bitrate = bitrate, option = option),
                qualityStatus = VideoQualityStatus.evaluate(width = width, height = height, bitrate = bitrate)
            )
    }
}

/**
 * MediaExtractor 트랙 mime 타입을 사람이 읽을 수 있는 코덱 이름으로 변환.
 * 가져오기 미리보기에서 원본 영상이 어떤 코덱인지 보여주기 위해 사용.
 */
object VideoCodecName {
    fun fromMime(mime: String?): String = when (mime) {
        null -> "코덱 정보 없음"
        "video/avc" -> "H.264 (AVC)"
        "video/hevc" -> "H.265 (HEVC)"
        "video/x-vnd.on2.vp8" -> "VP8"
        "video/x-vnd.on2.vp9" -> "VP9"
        "video/av01" -> "AV1"
        "video/mp4v-es" -> "MPEG-4"
        "video/3gpp" -> "H.263"
        else -> mime.substringAfter('/', mime).uppercase()
    }
}

object VideoImportFileName {
    fun choose(
        displayName: String?,
        mediaStoreName: String?,
        fallbackSegment: String?,
        timestampMillis: Long = System.currentTimeMillis()
    ): String {
        val candidates = listOf(
            displayName,
            mediaStoreName,
            fallbackSegment?.substringAfterLast('/')
        )
        val selected = candidates
            .mapNotNull { it?.trim()?.takeIf(String::isNotEmpty) }
            .firstOrNull { !it.isGeneratedPickerName() }

        return (selected ?: generatedName(timestampMillis)).sanitizeFileName()
    }

    fun compressedOutputName(originalName: String): String {
        val baseName = originalName
            .substringBeforeLast('.', originalName)
            .ifBlank { "Meet" }
            .sanitizeFileName()
        return "$baseName.mp4"
    }

    private fun generatedName(timestampMillis: Long): String =
        "Meet_${DATE_FORMAT.format(Date(timestampMillis))}.mp4"

    private fun String.isGeneratedPickerName(): Boolean {
        val baseName = substringBeforeLast('.', this)
        return baseName.length >= 6 && baseName.all { it.isDigit() }
    }

    private fun String.sanitizeFileName(): String =
        replace(Regex("[\\\\/:*?\"<>|]"), "_")
            .replace(Regex("\\s+"), " ")
            .trim()
            .ifBlank { generatedName(System.currentTimeMillis()) }

    private val DATE_FORMAT = SimpleDateFormat("yyyyMMdd_HHmmss", Locale.KOREA).apply {
        timeZone = TimeZone.getTimeZone("Asia/Seoul")
    }
}
