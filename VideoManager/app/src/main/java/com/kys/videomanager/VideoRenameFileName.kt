package com.kys.videomanager

object VideoRenameFileName {
    fun defaultEditableName(originalName: String): String =
        VideoTrimFileName.defaultEditableName(originalName)

    fun outputName(originalName: String, requestedName: String): String =
        VideoTrimFileName.outputName(originalName, requestedName)
}
