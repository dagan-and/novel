package com.kys.videomanager

import org.junit.Assert.assertEquals
import org.junit.Assert.assertFalse
import org.junit.Assert.assertTrue
import org.junit.Test

class MainScreenUiModelTest {

    @Test fun `main screen copy describes the video tab as the central library`() {
        assertEquals("영상 관리자", MainScreenUiModel.title)
        assertEquals(listOf("검색", "영상", "다운로드"), MainScreenUiModel.tabs)
        assertEquals("영상", MainScreenUiModel.selectedTab)
    }

    @Test fun `main pager uses three tabs with video selected by default`() {
        assertEquals(3, MainScreenUiModel.pageCount)
        assertEquals(1, MainScreenUiModel.defaultPageIndex)
        assertEquals("검색", MainScreenUiModel.tabTitle(0))
        assertEquals("영상", MainScreenUiModel.tabTitle(1))
        assertEquals("다운로드", MainScreenUiModel.tabTitle(2))
    }

    @Test fun `search page can navigate to product-code search url`() {
        assertEquals("https://avppomppu.com", MainScreenUiModel.productCodeHomeUrl)
        assertEquals("https://avdbapi.com", MainScreenUiModel.searchHomeUrl)
    }

    @Test fun `settings menu exposes video actions before player settings`() {
        assertEquals(
            listOf("가져오기", "편집하기", "파일명 변경", "플레이어 변경", "플레이어 초기화"),
            MainScreenUiModel.settingsOptions.toList()
        )
        assertFalse(MainScreenUiModel.settingsOptions.any { it.startsWith("기본 ") })
    }

    @Test fun `download summary reports active progress`() {
        val progress = HlsDownloadProgress(
            status = HlsDownloadStatus.DOWNLOADING,
            title = "sample_video.ts",
            downloadedSegments = 21,
            totalSegments = 50
        )

        assertEquals("다운로드 중 · 42%", MainScreenUiModel.downloadSummary(listOf(progress)))
    }

    @Test fun `download summary is hidden without active downloads`() {
        val progress = HlsDownloadProgress(
            status = HlsDownloadStatus.COMPLETED,
            title = "sample_video.ts",
            downloadedSegments = 50,
            totalSegments = 50
        )

        assertEquals(null, MainScreenUiModel.downloadSummary(listOf(progress)))
    }

    @Test fun `download page reminds user to use completed download actions`() {
        assertTrue(DownloadStatusUiModel.importReminder.contains("시청"))
        assertTrue(DownloadStatusUiModel.importReminder.contains("가져오기"))
    }

    @Test fun `download action buttons share compact row dimensions`() {
        assertEquals(44, DownloadActionButtonUiPolicy.heightDp)
        assertEquals(0, DownloadActionButtonUiPolicy.minWidthDp)
        assertEquals(0, DownloadActionButtonUiPolicy.minHeightDp)
        assertEquals(12, DownloadActionButtonUiPolicy.horizontalPaddingDp)
        assertEquals(8, DownloadActionButtonUiPolicy.cornerRadiusDp)
    }
}
