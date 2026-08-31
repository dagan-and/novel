package com.kys.videomanager.video

import org.json.JSONException
import org.junit.Assert.assertEquals
import org.junit.Assert.assertNull
import org.junit.Assert.assertTrue
import org.junit.Test

class RatingBackupSerializationTest {

    @Test fun `round trip preserves ratings and default player`() {
        val original = BackupData(
            ratings = mapOf("/a.mp4" to 4.5f, "/b.mp4" to 3.0f),
            defaultPlayerPackage = "com.mxtech.videoplayer.ad",
            defaultPlayerName = "MX Player"
        )

        val restored = deserializeBackup(serializeBackup(original))

        assertEquals(original.ratings, restored.ratings)
        assertEquals(original.defaultPlayerPackage, restored.defaultPlayerPackage)
        assertEquals(original.defaultPlayerName, restored.defaultPlayerName)
    }

    @Test fun `empty ratings and null default player round trip`() {
        val original = BackupData(ratings = emptyMap(), defaultPlayerPackage = null, defaultPlayerName = null)

        val restored = deserializeBackup(serializeBackup(original))

        assertTrue(restored.ratings.isEmpty())
        assertNull(restored.defaultPlayerPackage)
        assertNull(restored.defaultPlayerName)
    }

    @Test(expected = JSONException::class)
    fun `malformed json throws`() {
        deserializeBackup("not a json")
    }

    @Test fun `missing defaultPlayer key parses as null`() {
        val json = """{"version":1,"ratings":{"/a.mp4":5.0}}"""

        val restored = deserializeBackup(json)

        assertEquals(5.0f, restored.ratings["/a.mp4"])
        assertNull(restored.defaultPlayerPackage)
    }
}
