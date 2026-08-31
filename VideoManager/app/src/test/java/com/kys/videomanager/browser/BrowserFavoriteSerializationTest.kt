package com.kys.videomanager.browser

import org.json.JSONException
import org.junit.Assert.assertEquals
import org.junit.Assert.assertTrue
import org.junit.Test

class BrowserFavoriteSerializationTest {

    @Test fun `round trip preserves url and title`() {
        val original = listOf(
            BrowserFavorite(url = "https://example.com", title = "Example"),
            BrowserFavorite(url = "https://example.org/path?x=1", title = "Other Site")
        )

        val restored = deserializeFavorites(serializeFavorites(original))

        assertEquals(original, restored)
    }

    @Test fun `empty list round trips to empty list`() {
        val restored = deserializeFavorites(serializeFavorites(emptyList()))

        assertTrue(restored.isEmpty())
    }

    @Test fun `special characters in title and url round trip exactly`() {
        val original = listOf(
            BrowserFavorite(
                url = "https://example.com/a?b=\"c\"&d=<e>",
                title = "따옴표\"와 <꺾쇠> & 이모지 😀"
            )
        )

        val restored = deserializeFavorites(serializeFavorites(original))

        assertEquals(original, restored)
    }

    @Test(expected = JSONException::class)
    fun `malformed json throws`() {
        deserializeFavorites("not a json array")
    }

    @Test fun `entry missing url is skipped`() {
        val json = """[{"title":"no url here"},{"url":"https://example.com","title":"kept"}]"""

        val restored = deserializeFavorites(json)

        assertEquals(listOf(BrowserFavorite(url = "https://example.com", title = "kept")), restored)
    }

    @Test fun `missing title falls back to url`() {
        val json = """[{"url":"https://example.com"}]"""

        val restored = deserializeFavorites(json)

        assertEquals(listOf(BrowserFavorite(url = "https://example.com", title = "https://example.com")), restored)
    }
}
