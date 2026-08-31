package com.kys.videomanager.ffmpeg

object FfmpegRuntimeAvailability {
    fun isUnavailable(error: Throwable): Boolean =
        error is UnsatisfiedLinkError ||
            error is NoClassDefFoundError ||
            error is ExceptionInInitializerError
}
