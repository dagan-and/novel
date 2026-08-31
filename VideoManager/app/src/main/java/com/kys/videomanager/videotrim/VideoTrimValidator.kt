package com.kys.videomanager.videotrim

enum class VideoTrimValidationResult {
    Valid,
    EndBeforeStart,
    EndExceedsDuration
}

object VideoTrimValidator {
    private const val END_TIME_TOLERANCE_MS = 1_000L

    fun validate(
        startSeconds: Long,
        endSeconds: Long,
        videoDurationMs: Long
    ): VideoTrimValidationResult =
        when {
            endSeconds <= startSeconds -> VideoTrimValidationResult.EndBeforeStart
            videoDurationMs > 0L && endSeconds * 1000L > videoDurationMs + END_TIME_TOLERANCE_MS ->
                VideoTrimValidationResult.EndExceedsDuration
            else -> VideoTrimValidationResult.Valid
        }
}
