package com.kys.videomanager

object MainScreenUiModel {
    const val title = "영상 관리자"
    const val productCodeHomeUrl = "https://avppomppu.com"
    const val searchHomeUrl = "https://avdbapi.com"
    val tabs = listOf("검색", "영상", "다운로드")
    const val selectedTab = "영상"
    val pageCount: Int
        get() = tabs.size
    val defaultPageIndex: Int
        get() = tabs.indexOf(selectedTab).coerceAtLeast(0)
    val searchPageIndex: Int
        get() = tabs.indexOf("검색").coerceAtLeast(0)
    val downloadPageIndex: Int
        get() = tabs.indexOf("다운로드").coerceAtLeast(defaultPageIndex)
    val settingsOptions = arrayOf("가져오기", "편집하기", "파일명 변경", "플레이어 변경", "플레이어 초기화")

    fun tabTitle(index: Int): String =
        tabs[index]

    fun downloadSummary(progresses: List<HlsDownloadProgress>): String? {
        val active = progresses.firstOrNull { it.isActiveDownload() } ?: return null
        return "다운로드 중 · ${active.percent}%"
    }

    fun activeDownload(progresses: List<HlsDownloadProgress>): HlsDownloadProgress? =
        progresses.firstOrNull { it.isActiveDownload() }

    fun isActiveDownloadStatus(status: HlsDownloadStatus): Boolean =
        status == HlsDownloadStatus.FETCHING_PLAYLIST ||
            status == HlsDownloadStatus.DOWNLOADING ||
            status == HlsDownloadStatus.REMUXING

    private fun HlsDownloadProgress.isActiveDownload(): Boolean =
        isActiveDownloadStatus(status)
}

object DownloadStatusUiModel {
    const val importReminder = "완료된 다운로드는 시청하거나 가져오기 버튼으로 영상 목록에 추가할 수 있습니다."
}

object DownloadActionButtonUiPolicy {
    const val heightDp = 44
    const val minWidthDp = 0
    const val minHeightDp = 0
    const val horizontalPaddingDp = 12
    const val cornerRadiusDp = 8
}
