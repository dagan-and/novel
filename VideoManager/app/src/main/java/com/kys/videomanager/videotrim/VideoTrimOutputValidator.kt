package com.kys.videomanager.videotrim

import java.io.File

object VideoTrimOutputValidator {
    fun isUsable(file: File): Boolean = file.isFile && file.length() > 0L
}
