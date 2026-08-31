package com.kys.videomanager.video

import org.junit.Assert.assertFalse
import org.junit.Assert.assertTrue
import org.junit.Test

class RecentlyPlayedHighlightPolicyTest {

    @Test
    fun `item matching the last played path is highlighted`() {
        assertTrue(
            RecentlyPlayedHighlightPolicy.isHighlighted(
                itemPath = "/videos/a.mp4",
                lastPlayedPath = "/videos/a.mp4"
            )
        )
    }

    @Test
    fun `item not matching the last played path is not highlighted`() {
        assertFalse(
            RecentlyPlayedHighlightPolicy.isHighlighted(
                itemPath = "/videos/a.mp4",
                lastPlayedPath = "/videos/b.mp4"
            )
        )
    }

    @Test
    fun `no last played path highlights nothing`() {
        assertFalse(
            RecentlyPlayedHighlightPolicy.isHighlighted(
                itemPath = "/videos/a.mp4",
                lastPlayedPath = null
            )
        )
    }
}
