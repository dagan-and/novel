package com.kys.videomanager

import org.junit.Assert.assertEquals
import org.junit.Test

class HlsDownloadOutputPolicyTest {
    @Test
    fun downloadedHlsStreamsAreSavedAsTsBeforeImport() {
        assertEquals("ts", HlsDownloadOutputPolicy.downloadExtension)
    }

    @Test
    fun downloadedHlsStreamsUseSeparatePrivateDownloadArea() {
        assertEquals("downloads", HlsDownloadOutputPolicy.downloadDirectoryName)
    }

    @Test
    fun completedDownloadsExposeWatchAndImportActions() {
        assertEquals("시청", HlsDownloadOutputPolicy.watchActionLabel)
        assertEquals("가져오기", HlsDownloadOutputPolicy.importActionLabel)
    }
}
