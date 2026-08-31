package com.kys.videomanager

object FfmpegImportCommand {
    fun hardware(inputPath: String, outputPath: String, policy: VideoImportPolicy): Array<String> =
        baseArgs(inputPath, policy, videoCodec = "hevc_mediacodec") +
            arrayOf("-tag:v", "hvc1", "-movflags", "+faststart", outputPath)

    fun softwareFallback(inputPath: String, outputPath: String, policy: VideoImportPolicy): Array<String> =
        baseArgs(inputPath, policy, videoCodec = "libx265") +
            arrayOf("-preset", "veryfast", "-tag:v", "hvc1", "-movflags", "+faststart", outputPath)

    private fun baseArgs(
        inputPath: String,
        policy: VideoImportPolicy,
        videoCodec: String
    ): Array<String> =
        arrayOf(
            "-y",
            "-i", inputPath,
            "-vf", "scale='if(gt(iw\\,ih)\\,-2\\,min(iw\\,${policy.targetHeight}))':'if(gt(iw\\,ih)\\,min(ih\\,${policy.targetHeight})\\,-2)',format=nv12",
            "-r", policy.targetFrameRate.toString(),
            "-c:v", videoCodec,
            "-b:v", policy.targetBitrate.toKilobits(),
            "-maxrate", policy.targetBitrate.toKilobits(),
            "-bufsize", (policy.targetBitrate * 2).toKilobits(),
            "-c:a", "aac",
            "-b:a", "128k"
        )

    private fun Int.toKilobits(): String =
        "${this / 1_000}k"
}
