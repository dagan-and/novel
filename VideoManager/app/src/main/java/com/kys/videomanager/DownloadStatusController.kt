package com.kys.videomanager

import android.content.ActivityNotFoundException
import android.content.res.ColorStateList
import android.content.Intent
import android.net.Uri
import android.text.format.Formatter
import android.view.View
import android.widget.Button
import android.widget.LinearLayout
import android.widget.ProgressBar
import android.widget.TextView
import android.widget.Toast
import androidx.appcompat.app.AppCompatActivity
import androidx.core.content.FileProvider
import androidx.core.view.setPadding
import com.google.android.material.button.MaterialButton
import com.google.android.material.dialog.MaterialAlertDialogBuilder
import java.io.File

class DownloadStatusController(
    private val activity: AppCompatActivity,
    private val root: View,
    private val onClose: () -> Unit = { activity.finish() },
    private val onImportRequested: (String) -> Unit = {
        Toast.makeText(activity, "메인 화면에서 가져오기 옵션을 선택해 주세요.", Toast.LENGTH_SHORT).show()
    }
) {
    private lateinit var downloadListContainer: LinearLayout
    private var stopListening: (() -> Unit)? = null

    fun start() {
        downloadListContainer = root.findViewById(R.id.download_list_container)
        root.findViewById<TextView>(R.id.tv_download_import_reminder).text = DownloadStatusUiModel.importReminder
        root.findViewById<Button>(R.id.btn_close_download).setOnClickListener { onClose() }
    }

    fun resume() {
        HlsDownloadStore.initialize(activity.applicationContext)
        stopListening?.invoke()
        stopListening = HlsDownloadStore.listen { progresses ->
            activity.runOnUiThread { render(progresses) }
        }
    }

    fun pause() {
        stopListening?.invoke()
        stopListening = null
    }

    fun destroy() {
        pause()
    }

    private fun render(progresses: List<HlsDownloadProgress>) {
        downloadListContainer.removeAllViews()
        if (progresses.isEmpty()) {
            downloadListContainer.addView(TextView(activity).apply {
                text = "다운로드 상태가 없습니다."
                textSize = 15f
                setTextColor(0xFF52606D.toInt())
            })
        } else {
            progresses.asReversed().forEach { progress ->
                downloadListContainer.addView(createProgressView(progress))
            }
        }
    }

    private fun createProgressView(progress: HlsDownloadProgress): View {
        val density = activity.resources.displayMetrics.density
        return LinearLayout(activity).apply {
            orientation = LinearLayout.VERTICAL
            setPadding((14 * density).toInt())
            setBackgroundColor(0xFFFFFFFF.toInt())
            addView(TextView(activity).apply {
                text = progress.title.ifBlank { "다운로드" }
                textSize = 17f
                setTypeface(typeface, android.graphics.Typeface.BOLD)
                setTextColor(0xFF1F2933.toInt())
            })
            addView(TextView(activity).apply {
                text = progress.message
                textSize = 14f
                setTextColor(0xFF52606D.toInt())
                setPadding(0, (8 * density).toInt(), 0, 0)
            })
            addView(ProgressBar(activity, null, android.R.attr.progressBarStyleHorizontal).apply {
                max = 100
                this.progress = progress.percent
                setPadding(0, (14 * density).toInt(), 0, 0)
            })
            addView(TextView(activity).apply {
                text = progress.detailText()
                textSize = 14f
                setTextColor(0xFF334E68.toInt())
                setPadding(0, (10 * density).toInt(), 0, 0)
            })
            if (!progress.outputPath.isNullOrBlank()) {
                addView(TextView(activity).apply {
                    text = "저장 위치: ${progress.outputPath}"
                    textSize = 12f
                    setTextColor(0xFF6B7C8F.toInt())
                    setPadding(0, (12 * density).toInt(), 0, 0)
                })
            }
            addView(createActionRow(progress, density))
            layoutParams = LinearLayout.LayoutParams(
                LinearLayout.LayoutParams.MATCH_PARENT,
                LinearLayout.LayoutParams.WRAP_CONTENT
            ).apply {
                bottomMargin = (12 * density).toInt()
            }
        }
    }

    private fun createActionRow(progress: HlsDownloadProgress, density: Float): View =
        LinearLayout(activity).apply {
            orientation = LinearLayout.HORIZONTAL
            setPadding(0, (12 * density).toInt(), 0, 0)

            if (progress.canRetry()) {
                addView(actionButton("다시 시도") { HlsDownloadService.retry(activity, progress.id) })
            }
            if (progress.canCancel()) {
                addView(actionButton("취소", isDanger = true) { HlsDownloadService.cancel(activity, progress.id) })
            }
            if (progress.status == HlsDownloadStatus.COMPLETED && !progress.outputPath.isNullOrBlank()) {
                addView(actionButton(HlsDownloadOutputPolicy.watchActionLabel) { openDownloadedFile(progress.outputPath) })
                addView(actionButton(HlsDownloadOutputPolicy.importActionLabel) { onImportRequested(progress.outputPath) })
            }
            if (progress.canDelete()) {
                addView(actionButton("삭제", isDanger = true) { confirmAndDeleteDownload(progress) })
            }
        }

    private fun actionButton(textValue: String, isDanger: Boolean = false, onClick: () -> Unit): Button =
        MaterialButton(activity).apply {
            val density = activity.resources.displayMetrics.density
            text = textValue
            textSize = 13f
            minWidth = (DownloadActionButtonUiPolicy.minWidthDp * density).toInt()
            minimumWidth = minWidth
            minHeight = (DownloadActionButtonUiPolicy.minHeightDp * density).toInt()
            minimumHeight = minHeight
            insetTop = 0
            insetBottom = 0
            cornerRadius = (DownloadActionButtonUiPolicy.cornerRadiusDp * density).toInt()
            setPadding(
                (DownloadActionButtonUiPolicy.horizontalPaddingDp * density).toInt(),
                paddingTop,
                (DownloadActionButtonUiPolicy.horizontalPaddingDp * density).toInt(),
                paddingBottom
            )
            if (isDanger) {
                backgroundTintList = ColorStateList.valueOf(0xFFB42318.toInt())
                setTextColor(0xFFFFFFFF.toInt())
            } else {
                backgroundTintList = ColorStateList.valueOf(0xFF5F6368.toInt())
                setTextColor(0xFFFFFFFF.toInt())
            }
            setOnClickListener { onClick() }
            layoutParams = LinearLayout.LayoutParams(
                LinearLayout.LayoutParams.WRAP_CONTENT,
                (DownloadActionButtonUiPolicy.heightDp * density).toInt()
            ).apply {
                rightMargin = (8 * density).toInt()
            }
        }

    private fun openDownloadedFile(path: String) {
        val file = File(path)
        if (!file.exists()) {
            Toast.makeText(activity, "파일을 찾을 수 없습니다.", Toast.LENGTH_SHORT).show()
            return
        }
        val uri: Uri = FileProvider.getUriForFile(activity, "${activity.packageName}.fileprovider", file)
        val intent = Intent(Intent.ACTION_VIEW).apply {
            setDataAndType(uri, "video/*")
            addFlags(Intent.FLAG_GRANT_READ_URI_PERMISSION)
        }
        try {
            activity.startActivity(Intent.createChooser(intent, "파일 열기"))
        } catch (_: ActivityNotFoundException) {
            Toast.makeText(activity, "열 수 있는 앱이 없습니다.", Toast.LENGTH_SHORT).show()
        } catch (e: Exception) {
            Toast.makeText(activity, "파일 열기 실패: ${e.message ?: e.javaClass.simpleName}", Toast.LENGTH_SHORT).show()
        }
    }

    private fun confirmAndDeleteDownload(progress: HlsDownloadProgress) {
        MaterialAlertDialogBuilder(activity)
            .setTitle("파일 삭제")
            .setMessage("「${progress.title}」을 삭제하시겠습니까?\n이 작업은 되돌릴 수 없습니다.")
            .setPositiveButton("삭제") { _, _ -> deleteDownload(progress) }
            .setNegativeButton("취소", null)
            .show()
    }

    private fun deleteDownload(progress: HlsDownloadProgress) {
        progress.outputPath
            ?.takeIf { it.isNotBlank() }
            ?.let { File(it) }
            ?.takeIf { it.exists() }
            ?.delete()
        File(activity.cacheDir, "hls/${progress.id}.ts").delete()
        HlsDownloadStore.remove(progress.id)
        Toast.makeText(activity, "삭제했습니다.", Toast.LENGTH_SHORT).show()
    }

    private fun HlsDownloadProgress.detailText(): String = buildString {
        append("${percent}%")
        if (totalSegments > 0) {
            append(" · ${downloadedSegments}/${totalSegments} 세그먼트")
        }
        if (downloadedBytes > 0) {
            append(" · ${Formatter.formatFileSize(activity, downloadedBytes)}")
        }
    }

    private fun HlsDownloadProgress.isRunning(): Boolean =
        when (status) {
            HlsDownloadStatus.FETCHING_PLAYLIST,
            HlsDownloadStatus.DOWNLOADING,
            HlsDownloadStatus.REMUXING -> true
            else -> false
        }

    private fun HlsDownloadProgress.canCancel(): Boolean =
        isRunning() || status == HlsDownloadStatus.IDLE

    private fun HlsDownloadProgress.canRetry(): Boolean =
        status == HlsDownloadStatus.FAILED ||
            status == HlsDownloadStatus.CANCELED ||
            status == HlsDownloadStatus.IDLE

    private fun HlsDownloadProgress.canDelete(): Boolean =
        status == HlsDownloadStatus.COMPLETED ||
            status == HlsDownloadStatus.FAILED ||
            status == HlsDownloadStatus.CANCELED
}
