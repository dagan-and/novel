package com.kys.videomanager

import org.junit.Assert.assertEquals
import org.junit.Test

class VideoSourceDeletionPolicyTest {

    @Test
    fun `successful imports delete their original sources and keep failed deletes non-fatal`() {
        val attemptedIndexes = mutableListOf<Int>()

        val summary = VideoSourceDeletionPolicy.deleteImportedSources(sourceCount = 3) { index ->
            attemptedIndexes += index
            index != 1
        }

        assertEquals(listOf(0, 1, 2), attemptedIndexes)
        assertEquals(2, summary.deletedCount)
        assertEquals(1, summary.failedCount)
    }
}
