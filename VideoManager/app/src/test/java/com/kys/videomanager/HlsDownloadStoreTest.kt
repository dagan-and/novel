package com.kys.videomanager

import org.junit.Assert.assertEquals
import org.junit.Assert.assertTrue
import org.junit.Test

class HlsDownloadStoreTest {

    @Test fun `store keeps multiple download progresses by id`() {
        HlsDownloadStore.clearForTest()

        HlsDownloadStore.update(
            HlsDownloadProgress(
                id = "one",
                status = HlsDownloadStatus.DOWNLOADING,
                title = "one",
                playlistUrl = "https://example.com/one.m3u8"
            )
        )
        HlsDownloadStore.update(
            HlsDownloadProgress(
                id = "two",
                status = HlsDownloadStatus.DOWNLOADING,
                title = "two",
                playlistUrl = "https://example.com/two.m3u8"
            )
        )

        assertEquals(listOf("one", "two"), HlsDownloadStore.snapshot().map { it.id })
    }

    @Test fun `listener receives full progress list`() {
        HlsDownloadStore.clearForTest()
        val snapshots = mutableListOf<List<HlsDownloadProgress>>()

        val stop = HlsDownloadStore.listen { snapshots += it }
        HlsDownloadStore.update(
            HlsDownloadProgress(
                id = "one",
                status = HlsDownloadStatus.COMPLETED,
                title = "one",
                playlistUrl = "https://example.com/one.m3u8"
            )
        )
        stop()

        assertTrue(snapshots.first().isEmpty())
        assertEquals(listOf("one"), snapshots.last().map { it.id })
    }

    @Test fun `pending requests are dequeued in order`() {
        HlsDownloadStore.clearForTest()
        val first = HlsDownloadRequest(
            id = "first",
            playlistUrl = "https://example.com/first.m3u8",
            pageUrl = null,
            requestHeaders = emptyMap(),
            cookie = null,
            title = "first"
        )
        val second = first.copy(id = "second", title = "second")

        HlsDownloadStore.enqueue(first)
        HlsDownloadStore.enqueue(second)

        assertEquals("first", HlsDownloadStore.dequeue()?.id)
        assertEquals("second", HlsDownloadStore.dequeue()?.id)
    }

    @Test fun `retry queue keeps resumable progress fields`() {
        HlsDownloadStore.clearForTest()
        val request = HlsDownloadRequest(
            id = "retry",
            playlistUrl = "https://example.com/video.m3u8",
            pageUrl = null,
            requestHeaders = emptyMap(),
            cookie = null,
            title = "video"
        )
        HlsDownloadStore.update(
            HlsDownloadProgress(
                id = request.id,
                status = HlsDownloadStatus.FAILED,
                title = request.title,
                playlistUrl = request.playlistUrl,
                downloadedSegments = 7,
                totalSegments = 12,
                downloadedBytes = 4096L,
                outputPath = "/downloads/video.ts",
                message = "다운로드 실패",
                request = request
            )
        )

        HlsDownloadStore.markRetryQueued(request)

        val progress = HlsDownloadStore.snapshot().single()
        assertEquals(HlsDownloadStatus.IDLE, progress.status)
        assertEquals(7, progress.downloadedSegments)
        assertEquals(12, progress.totalSegments)
        assertEquals(4096L, progress.downloadedBytes)
        assertEquals("/downloads/video.ts", progress.outputPath)
        assertEquals(request, progress.request)
    }

    @Test fun `status updates keep resumable fields when retry has started`() {
        HlsDownloadStore.clearForTest()
        val request = HlsDownloadRequest(
            id = "retry",
            playlistUrl = "https://example.com/video.m3u8",
            pageUrl = null,
            requestHeaders = emptyMap(),
            cookie = null,
            title = "video"
        )
        HlsDownloadStore.update(
            HlsDownloadProgress(
                id = request.id,
                status = HlsDownloadStatus.IDLE,
                title = request.title,
                playlistUrl = request.playlistUrl,
                downloadedSegments = 7,
                totalSegments = 12,
                downloadedBytes = 4096L,
                outputPath = "/downloads/video.ts",
                message = "다운로드 재시도 대기 중",
                request = request
            )
        )

        HlsDownloadStore.update(
            HlsDownloadProgress(
                id = request.id,
                status = HlsDownloadStatus.FETCHING_PLAYLIST,
                title = request.title,
                playlistUrl = request.playlistUrl,
                message = "playlist 확인 중",
                request = request
            )
        )

        val progress = HlsDownloadStore.snapshot().single()
        assertEquals(HlsDownloadStatus.FETCHING_PLAYLIST, progress.status)
        assertEquals(7, progress.downloadedSegments)
        assertEquals(12, progress.totalSegments)
        assertEquals(4096L, progress.downloadedBytes)
        assertEquals("/downloads/video.ts", progress.outputPath)
    }

    @Test fun `remove drops the entry and notifies listeners`() {
        HlsDownloadStore.clearForTest()
        HlsDownloadStore.update(
            HlsDownloadProgress(
                id = "done",
                status = HlsDownloadStatus.COMPLETED,
                title = "done",
                playlistUrl = "https://example.com/done.m3u8",
                outputPath = "/downloads/done.ts"
            )
        )
        val snapshots = mutableListOf<List<HlsDownloadProgress>>()
        val stop = HlsDownloadStore.listen { snapshots += it }

        HlsDownloadStore.remove("done")
        stop()

        assertTrue(HlsDownloadStore.snapshot().isEmpty())
        assertTrue(snapshots.last().isEmpty())
    }
}
