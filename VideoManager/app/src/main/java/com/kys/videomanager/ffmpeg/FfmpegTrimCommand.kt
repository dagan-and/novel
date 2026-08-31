package com.kys.videomanager.ffmpeg
import com.kys.videomanager.videotrim.VideoTrimTime

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
