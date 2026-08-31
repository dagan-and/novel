package com.kys.videomanager.video

import android.content.Context
import android.graphics.Bitmap
import java.io.File
import java.security.MessageDigest

object VideoThumbnailCache {
    private const val DIRECTORY_NAME = "video_thumbnails"
    private const val JPEG_QUALITY = 82
    private const val DEFAULT_MAX_BYTES = 80L * 1024L * 1024L

    fun fileNameFor(path: String, dateModified: Long, size: Long): String {
        val identity = "$dateModified|$size"
        val identityDigest = MessageDigest.getInstance("SHA-256")
            .digest(identity.toByteArray(Charsets.UTF_8))
            .joinToString(separator = "") { byte -> "%02x".format(byte) }
            .take(16)
        return "${stablePathDigest(path)}_$identityDigest.jpg"
    }

    fun fileFor(context: Context, item: VideoItem): File {
        return fileForCacheRoot(context.cacheDir, item)
    }

    fun directoryForCacheRoot(cacheRoot: File): File =
        File(cacheRoot, DIRECTORY_NAME)

    fun fileForCacheRoot(cacheRoot: File, item: VideoItem): File {
        val directory = directoryForCacheRoot(cacheRoot).apply { if (!exists()) mkdirs() }
        return File(directory, fileNameFor(item.path, item.dateModified, item.size))
    }

    fun existingFileFor(context: Context, item: VideoItem): File? =
        fileFor(context, item).takeIf { it.isFile && it.length() > 0L }

    fun save(bitmap: Bitmap, outputFile: File): File? =
        runCatching {
            outputFile.parentFile?.mkdirs()
            outputFile.outputStream().use { output ->
                bitmap.compress(Bitmap.CompressFormat.JPEG, JPEG_QUALITY, output)
            }
            outputFile.takeIf { it.isFile && it.length() > 0L }
        }.getOrNull()

    fun deleteFor(context: Context, item: VideoItem): Int =
        deleteFor(context.cacheDir, item)

    fun deleteFor(cacheRoot: File, item: VideoItem): Int {
        val directory = directoryForCacheRoot(cacheRoot)
        val pathDigestPrefix = stablePathDigest(item.path)
        return directory
            .listFiles { file -> file.isFile && file.name.startsWith(pathDigestPrefix) }
            .orEmpty()
            .count { file -> file.delete() }
    }

    fun prune(context: Context, maxBytes: Long = DEFAULT_MAX_BYTES): Int =
        prune(context.cacheDir, maxBytes)

    fun prune(cacheRoot: File, maxBytes: Long = DEFAULT_MAX_BYTES): Int {
        val files = directoryForCacheRoot(cacheRoot)
            .listFiles { file -> file.isFile && file.extension.equals("jpg", ignoreCase = true) }
            .orEmpty()
            .sortedBy { it.lastModified() }
            .toMutableList()
        var totalBytes = files.sumOf { it.length() }
        var deleted = 0
        for (file in files) {
            if (totalBytes <= maxBytes) break
            val size = file.length()
            if (file.delete()) {
                totalBytes -= size
                deleted++
            }
        }
        return deleted
    }

    private fun stablePathDigest(path: String): String =
        MessageDigest.getInstance("SHA-256")
            .digest(path.toByteArray(Charsets.UTF_8))
            .joinToString(separator = "") { byte -> "%02x".format(byte) }
            .take(16)
}
