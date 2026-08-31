package com.kys.videomanager

object FfmpegRuntimeAvailability {
    fun isUnavailable(error: Throwable): Boolean =
        error is UnsatisfiedLinkError ||
            error is NoClassDefFoundError ||
            error is ExceptionInInitializerError
}
