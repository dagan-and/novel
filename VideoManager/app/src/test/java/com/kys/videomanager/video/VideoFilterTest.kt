package com.kys.videomanager.video

import org.junit.Assert.assertEquals
import org.junit.Test

class VideoFilterTest {

    private fun item(path: String, rating: Float) =
        VideoItem(name = path, path = path, duration = 0, size = 0, dateModified = 0, rating = rating)

    private val videos = listOf(
        item("a", 5f),
        item("b", 4.5f),
        item("c", 4.0f),
        item("d", 3.0f),
        item("e", 2.0f),
        item("f", 2.5f),
        item("g", 1.0f),
        item("h", 0f),
        item("i", 0f)
    )

    @Test fun `ALL returns all videos`() {
        assertEquals(9, filterVideos(videos, RatingFilter.ALL).size)
    }

    @Test fun `Stars 5 returns only rating exactly 5`() {
        val result = filterVideos(videos, RatingFilter.Stars(5))
        assertEquals(1, result.size)
        assertEquals("a", result[0].path)
    }

    @Test fun `Stars 4 returns rating 4_0 to 4_9`() {
        val result = filterVideos(videos, RatingFilter.Stars(4))
        assertEquals(2, result.size) // b(4.5), c(4.0)
    }

    @Test fun `Stars 1 returns rating 1_0 to 1_9`() {
        val result = filterVideos(videos, RatingFilter.Stars(1))
        assertEquals(1, result.size)
        assertEquals("g", result[0].path)
    }

    @Test fun `Stars 2 returns rating 2_0 to 2_9`() {
        val result = filterVideos(videos, RatingFilter.Stars(2))
        assertEquals(listOf("e", "f"), result.map { it.path })
    }

    @Test fun `UNRATED returns rating 0`() {
        val result = filterVideos(videos, RatingFilter.UNRATED)
        assertEquals(2, result.size) // h, i
    }

    @Test fun `filter preference round trips selected filters`() {
        assertEquals(RatingFilter.ALL, ratingFilterFromPreferenceValue("all"))
        assertEquals(RatingFilter.UNRATED, ratingFilterFromPreferenceValue("unrated"))
        assertEquals(RatingFilter.Stars(2), ratingFilterFromPreferenceValue("stars:2"))
        assertEquals("stars:2", RatingFilter.Stars(2).toPreferenceValue())
    }

    @Test fun `invalid filter preference falls back to all`() {
        assertEquals(RatingFilter.ALL, ratingFilterFromPreferenceValue(null))
        assertEquals(RatingFilter.ALL, ratingFilterFromPreferenceValue("stars:0"))
        assertEquals(RatingFilter.ALL, ratingFilterFromPreferenceValue("stars:6"))
        assertEquals(RatingFilter.ALL, ratingFilterFromPreferenceValue("surprise"))
    }

    @Test fun `empty input always returns empty`() {
        assertEquals(0, filterVideos(emptyList(), RatingFilter.Stars(3)).size)
        assertEquals(0, filterVideos(emptyList(), RatingFilter.UNRATED).size)
        assertEquals(0, filterVideos(emptyList(), RatingFilter.ALL).size)
    }
}
