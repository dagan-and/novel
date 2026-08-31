package com.kys.videomanager

import org.junit.Assert.assertEquals
import org.junit.Assert.assertNotEquals
import org.junit.Assert.assertTrue
import org.junit.Test
import java.io.File
import kotlin.io.path.createTempDirectory

class VideoThumbnailCacheTest {

    @Test fun `same file identity uses same thumbnail cache name`() {
        val first = VideoThumbnailCache.fileNameFor(
            path = "/videos/sample.mp4",
            dateModified = 1234L,
            size = 5678L
        )
        val second = VideoThumbnailCache.fileNameFor(
            path = "/videos/sample.mp4",
            dateModified = 1234L,
            size = 5678L
        )

        assertEquals(first, second)
        assertTrue(first.endsWith(".jpg"))
    }

    @Test fun `changed file identity uses different thumbnail cache name`() {
        val original = VideoThumbnailCache.fileNameFor(
            path = "/videos/sample.mp4",
            dateModified = 1234L,
            size = 5678L
        )
        val modified = VideoThumbnailCache.fileNameFor(
            path = "/videos/sample.mp4",
            dateModified = 1235L,
            size = 5678L
        )
        val resized = VideoThumbnailCache.fileNameFor(
            path = "/videos/sample.mp4",
            dateModified = 1234L,
            size = 9999L
        )

        assertNotEquals(original, modified)
        assertNotEquals(original, resized)
    }

    @Test fun `delete removes every cached thumbnail for the same video path`() {
        val cacheRoot = createTempDirectory(prefix = "thumbnail-cache-test").toFile()
        val item = VideoItem(
            name = "강아지.mp4",
            path = "/videos/강아지.mp4",
            duration = 1_000L,
            size = 10L,
            dateModified = 100L
        )
        val oldCache = VideoThumbnailCache.fileForCacheRoot(cacheRoot, item.copy(dateModified = 90L))
        val currentCache = VideoThumbnailCache.fileForCacheRoot(cacheRoot, item)
        oldCache.parentFile?.mkdirs()
        oldCache.writeText("old")
        currentCache.writeText("current")

        val deleted = VideoThumbnailCache.deleteFor(cacheRoot, item)

        assertEquals(2, deleted)
        assertTrue(!oldCache.exists())
        assertTrue(!currentCache.exists())
        cacheRoot.deleteRecursively()
    }

    @Test fun `prune deletes oldest thumbnails when cache is over size limit`() {
        val cacheRoot = createTempDirectory(prefix = "thumbnail-cache-prune-test").toFile()
        val directory = VideoThumbnailCache.directoryForCacheRoot(cacheRoot)
        directory.mkdirs()
        val older = File(directory, "older.jpg").apply {
            writeText("12345")
            setLastModified(100L)
        }
        val newer = File(directory, "newer.jpg").apply {
            writeText("12345")
            setLastModified(200L)
        }

        val deleted = VideoThumbnailCache.prune(cacheRoot, maxBytes = 5L)

        assertEquals(1, deleted)
        assertTrue(!older.exists())
        assertTrue(newer.exists())
        cacheRoot.deleteRecursively()
    }
}
