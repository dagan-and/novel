package com.kys.videomanager

import org.junit.Assert.assertTrue
import org.junit.Test
import java.nio.file.Files
import java.nio.file.Path
import java.nio.file.Paths

class MainTabResourceTest {

    @Test fun `main tabs render as filled segmented control`() {
        val layout = readResource("layout/activity_main.xml")

        assertTrue(layout.contains("app:tabGravity=\"fill\""))
        assertTrue(layout.contains("app:tabIndicatorHeight=\"0dp\""))
        assertTrue(layout.contains("app:tabBackground=\"@drawable/bg_main_tab_item\""))
        assertTrue(Files.exists(resourcePath("drawable/bg_main_tabs_container.xml")))
        assertTrue(Files.exists(resourcePath("drawable/bg_main_tab_item.xml")))
    }

    @Test fun `selected main tab background fills the tab cell`() {
        val layout = readResource("layout/activity_main.xml")

        assertTrue(layout.contains("android:padding=\"0dp\""))
    }

    private fun readResource(relativePath: String): String =
        String(Files.readAllBytes(resourcePath(relativePath)))

    private fun resourcePath(relativePath: String): Path {
        val candidates = listOf(
            Paths.get("app/src/main/res/$relativePath"),
            Paths.get("src/main/res/$relativePath")
        )
        return candidates.firstOrNull { Files.exists(it) }
            ?: error("Missing resource: $relativePath")
    }
}
