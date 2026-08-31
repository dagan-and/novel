package com.kys.videomanager

object FfmpegTrimCommand {
    fun fastCopy(
        inputPath: String,
        outputPath: String,
        startSeconds: Long,
        endSeconds: Long
    ): Array<String> =
        arrayOf(
            "-y",
            "-ss", VideoTrimTime.formatTimestamp(startSeconds),
            "-i", inputPath,
            "-t", VideoTrimTime.formatTimestamp(endSeconds - startSeconds),
            "-c", "copy",
            "-avoid_negative_ts", "make_zero",
            outputPath
        )
}
