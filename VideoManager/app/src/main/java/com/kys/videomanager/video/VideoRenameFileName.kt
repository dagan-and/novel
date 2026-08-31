package com.kys.videomanager.video
import com.kys.videomanager.videotrim.VideoTrimFileName

object VideoRenameFileName {
    fun defaultEditableName(originalName: String): String =
        VideoTrimFileName.defaultEditableName(originalName)

    fun outputName(originalName: String, requestedName: String): String =
        VideoTrimFileName.outputName(originalName, requestedName)
}
