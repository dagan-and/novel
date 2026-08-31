package com.kys.videomanager.video

import org.junit.Assert.assertEquals
import org.junit.Test

class VideoListUiStateTest {

    @Test fun `rating preference key uses file name instead of absolute path`() {
        val item = VideoItem(
            name = "SHKD-592.mkv",
            path = "/storage/emulated/0/Android/data/com.kys/files/videos/SHKD-592.mkv",
            duration = 0L,
            size = 0L,
            dateModified = 0L
        )

        assertEquals("SHKD-592.mkv", item.ratingPreferenceKey())
    }

    @Test fun `file size is displayed in gb`() {
        assertEquals("2.7 GB", VideoListFormatter.formatSize(2_915_660_800L))
    }

    @Test fun `sort mode labels expose current selection`() {
        assertEquals("별점순", VideoSortMode.RATING_DESC.label)
        assertEquals("최신순", VideoSortMode.NEWEST_FIRST.label)
    }
}
