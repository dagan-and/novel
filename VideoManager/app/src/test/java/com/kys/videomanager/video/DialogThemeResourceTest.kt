package com.kys.videomanager.video

import org.junit.Assert.assertTrue
import org.junit.Test
import java.nio.file.Files
import java.nio.file.Path
import java.nio.file.Paths

class DialogThemeResourceTest {

    @Test
    fun `app theme points material dialogs to the custom dialog overlay`() {
        val valuesTheme = readResource("values/themes.xml")
        val nightTheme = readResource("values-night/themes.xml")

        assertTrue(
            valuesTheme.contains("<item name=\"materialAlertDialogTheme\">@style/ThemeOverlay.VideoManager.Dialog</item>")
        )
        assertTrue(
            nightTheme.contains("<item name=\"materialAlertDialogTheme\">@style/ThemeOverlay.VideoManager.Dialog</item>")
        )
    }

    @Test
    fun `custom dialog overlay defines rounded background and button styles`() {
        val valuesTheme = readResource("values/themes.xml")

        assertTrue(valuesTheme.contains("<style name=\"ThemeOverlay.VideoManager.Dialog\""))
        assertTrue(valuesTheme.contains("<item name=\"android:windowBackground\">@drawable/bg_dialog_window</item>"))
        assertTrue(valuesTheme.contains("<item name=\"buttonBarPositiveButtonStyle\">@style/Widget.VideoManager.Dialog.PositiveButton</item>"))
        assertTrue(valuesTheme.contains("<item name=\"buttonBarNegativeButtonStyle\">@style/Widget.VideoManager.Dialog.NegativeButton</item>"))
        assertTrue(Files.exists(resourcePath("drawable/bg_dialog_window.xml")))
    }

    @Test
    fun `dialog button styles keep alert dialog layout dimensions`() {
        val valuesTheme = readResource("values/themes.xml")

        assertTrue(valuesTheme.contains("<item name=\"android:layout_width\">wrap_content</item>"))
        assertTrue(valuesTheme.contains("<item name=\"android:layout_height\">wrap_content</item>"))
    }

    @Test
    fun `dialog title style keeps alert dialog layout dimensions`() {
        val valuesTheme = readResource("values/themes.xml")

        assertTrue(
            valuesTheme.contains("<style name=\"TextAppearance.VideoManager.Dialog.Title\" parent=\"MaterialAlertDialog.MaterialComponents.Title.Text\">")
        )
    }

    @Test
    fun `status bar is black in day and night themes`() {
        val valuesTheme = readResource("values/themes.xml")
        val nightTheme = readResource("values-night/themes.xml")

        assertTrue(valuesTheme.contains("<item name=\"android:statusBarColor\">@color/black</item>"))
        assertTrue(nightTheme.contains("<item name=\"android:statusBarColor\">@color/black</item>"))
    }

    @Test
    fun `bottom sheet forces a light surface regardless of day-night theme`() {
        val valuesTheme = readResource("values/themes.xml")
        val mainActivity = String(Files.readAllBytes(sourcePath("MainActivity.kt")))

        assertTrue(valuesTheme.contains("<style name=\"ThemeOverlay.VideoManager.BottomSheet\""))
        assertTrue(valuesTheme.contains("<style name=\"Widget.VideoManager.BottomSheet\" parent=\"Widget.MaterialComponents.BottomSheet.Modal\">"))
        assertTrue(valuesTheme.contains("<item name=\"backgroundTint\">@color/surface</item>"))
        assertTrue(mainActivity.contains("BottomSheetDialog(this, R.style.ThemeOverlay_VideoManager_BottomSheet)"))
    }

    @Test
    fun `main dialogs use custom choice rows instead of platform single choice items`() {
        val mainActivity = String(Files.readAllBytes(sourcePath("MainActivity.kt")))

        assertTrue(!mainActivity.contains(".setSingleChoiceItems("))
        assertTrue(mainActivity.contains("createDialogChoiceRow("))
    }

    @Test
    fun `import flow exposes bitrate slider and progress dialog`() {
        val mainActivity = String(Files.readAllBytes(sourcePath("MainActivity.kt")))

        assertTrue(mainActivity.contains("Slider(this@MainActivity)"))
        assertTrue(mainActivity.contains("showImportProgressDialog("))
        assertTrue(mainActivity.contains("updateImportProgress("))
    }

    @Test
    fun `download import button opens the normal import option flow`() {
        val controller = String(Files.readAllBytes(sourcePath("DownloadStatusController.kt")))
        val mainActivity = String(Files.readAllBytes(sourcePath("MainActivity.kt")))

        assertTrue(controller.contains("onImportRequested(progress.outputPath)"))
        assertTrue(!controller.contains("source.copyTo(target, overwrite = false)"))
        assertTrue(mainActivity.contains("showImportOptions(listOf(Uri.fromFile(File(path))), deleteSourceAfterImport = false)"))
    }

    @Test
    fun `main start does not reload the video list without data changes`() {
        val mainActivity = String(Files.readAllBytes(sourcePath("MainActivity.kt")))
        val onStartBody = mainActivity.substringAfter("override fun onStart()").substringBefore("override fun onStop()")

        assertTrue(!onStartBody.contains("loadVideos()"))
        assertTrue(mainActivity.contains("intent?.action == VideoImportService.ACTION_IMPORT_CHANGED"))
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

    private fun sourcePath(fileName: String): Path {
        val roots = listOf(
            Paths.get("app/src/main/java/com/kys/videomanager"),
            Paths.get("src/main/java/com/kys/videomanager")
        )
        for (root in roots) {
            if (!Files.exists(root)) continue
            Files.walk(root).use { stream ->
                val match = stream.filter { it.fileName.toString() == fileName }.findFirst()
                if (match.isPresent) return match.get()
            }
        }
        error("Missing source: $fileName")
    }
}
