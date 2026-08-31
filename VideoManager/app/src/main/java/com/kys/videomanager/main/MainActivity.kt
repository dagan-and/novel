package com.kys.videomanager.main
import com.kys.videomanager.video.filterVideos
import com.kys.videomanager.video.ratingPreferenceKey

import com.kys.videomanager.browser.BrowserPreferenceManager
import com.kys.videomanager.browser.BrowserWebViewController
import com.kys.videomanager.downloadstatus.DownloadStatusController
import com.kys.videomanager.ffmpeg.FfmpegImportCommand
import com.kys.videomanager.ffmpeg.FfmpegRuntimeAvailability
import com.kys.videomanager.hls.HlsDownloadOutputPolicy
import com.kys.videomanager.hls.HlsDownloadProgress
import com.kys.videomanager.hls.HlsDownloadStore
import com.kys.videomanager.video.RatingBackupManager
import com.kys.videomanager.video.VideoAdapter
import com.kys.videomanager.video.VideoFileNameSanitizer
import com.kys.videomanager.video.VideoItem
import com.kys.videomanager.video.VideoPreferenceManager
import com.kys.videomanager.video.VideoRenameFileName
import com.kys.videomanager.video.VideoThumbnailCache
import com.kys.videomanager.videoimport.VideoImportFileName
import com.kys.videomanager.videoimport.VideoImportItem
import com.kys.videomanager.videoimport.VideoImportOption
import com.kys.videomanager.videoimport.VideoImportPolicy
import com.kys.videomanager.videoimport.VideoImportPreview
import com.kys.videomanager.videoimport.VideoImportRequest
import com.kys.videomanager.videoimport.VideoImportService
import com.kys.videomanager.videotrim.VideoTrimFileName
import com.kys.videomanager.videotrim.VideoTrimRequest
import com.kys.videomanager.videotrim.VideoTrimService
import com.kys.videomanager.videotrim.VideoTrimTime
import com.kys.videomanager.videotrim.VideoTrimValidationResult
import com.kys.videomanager.videotrim.VideoTrimValidator
import com.kys.videomanager.R
import com.kys.videomanager.BuildConfig
import com.kys.videomanager.update.ForceUpdateDecision
import com.kys.videomanager.update.ForceUpdateGate
import com.kys.videomanager.update.ForceUpdateResult
import com.kys.videomanager.update.NetworkConnectivityGate
import com.kys.videomanager.video.RatingFilter
import com.kys.videomanager.video.VideoSortMode
import com.kys.videomanager.video.VideoSourceDeletionSummary

import android.Manifest
import android.content.BroadcastReceiver
import android.content.Context
import android.content.Intent
import android.content.IntentFilter
import android.content.res.ColorStateList
import android.content.pm.PackageManager
import android.content.pm.ResolveInfo
import android.graphics.Bitmap
import android.media.MediaExtractor
import android.media.MediaFormat
import android.media.MediaMetadataRetriever
import android.net.ConnectivityManager
import android.net.Uri
import android.os.Build
import android.os.Bundle
import android.os.Environment
import android.provider.DocumentsContract
import android.provider.Settings
import android.text.InputType
import android.text.TextUtils
import android.text.format.Formatter
import android.view.Gravity
import android.view.LayoutInflater
import android.view.View
import android.view.ViewGroup
import android.view.WindowManager
import android.widget.Button
import android.widget.EditText
import android.widget.ImageView
import android.widget.LinearLayout
import android.widget.ProgressBar
import android.widget.RadioButton
import android.widget.ScrollView
import android.widget.TextView
import android.widget.Toast
import androidx.activity.OnBackPressedCallback
import androidx.activity.result.contract.ActivityResultContracts
import androidx.appcompat.app.AlertDialog
import androidx.appcompat.app.AppCompatActivity
import androidx.biometric.BiometricManager
import androidx.biometric.BiometricPrompt
import androidx.core.content.FileProvider
import androidx.core.content.ContextCompat
import androidx.core.view.setPadding
import androidx.lifecycle.Lifecycle
import androidx.lifecycle.LifecycleEventObserver
import androidx.lifecycle.LifecycleOwner
import androidx.media3.common.Effect
import androidx.media3.common.MediaItem
import androidx.media3.common.MimeTypes
import androidx.media3.common.audio.AudioProcessor
import androidx.media3.effect.Presentation
import androidx.media3.transformer.Composition
import androidx.media3.transformer.DefaultEncoderFactory
import androidx.media3.transformer.EditedMediaItem
import androidx.media3.transformer.Effects
import androidx.media3.transformer.ExportException
import androidx.media3.transformer.ExportResult
import androidx.media3.transformer.ProgressHolder
import androidx.media3.transformer.Transformer
import androidx.media3.transformer.VideoEncoderSettings
import androidx.recyclerview.widget.LinearLayoutManager
import androidx.recyclerview.widget.RecyclerView
import androidx.viewpager2.widget.ViewPager2
import com.arthenica.ffmpegkit.FFmpegKit
import com.arthenica.ffmpegkit.ReturnCode
import com.bumptech.glide.Glide
import com.bumptech.glide.load.resource.bitmap.CenterCrop
import com.bumptech.glide.load.resource.bitmap.RoundedCorners
import com.bumptech.glide.request.RequestOptions
import com.google.android.material.bottomsheet.BottomSheetDialog
import com.google.android.material.dialog.MaterialAlertDialogBuilder
import com.google.android.material.slider.Slider
import com.google.android.material.tabs.TabLayout
import com.google.android.material.tabs.TabLayoutMediator
import com.google.android.material.textfield.TextInputEditText
import com.google.android.material.textfield.TextInputLayout
import kotlinx.coroutines.*
import java.io.File
import kotlin.coroutines.resume

/**
 * 로컬 영상 파일 관리 앱 – 메인 액티비티
 *
 * 주요 기능:
 *  1. 파일피커로 영상을 가져와 앱 전용 저장소(getExternalFilesDir/videos)에 보관 – 별도 미디어 접근 권한 불필요,
 *     갤러리/파일 앱에는 노출되지 않음.
 *  2. Coroutine(IO) 으로 폴더 스캔 비동기 처리
 *  3. RecyclerView + VideoAdapter 로 영상 목록 표시
 *  4. 앱 시작 시 최신순 정렬
 *  5. 랜덤 버튼 → 리스트 랜덤 섞기
 *  6. 별점 버튼 → 별점 필터 선택 + 별점순 정렬
 *  7. 최신순 버튼 → 최신순/오래된순 정렬 선택
 *  8. ⚙️ 버튼 → 기본 플레이어 선택/초기화 팝업
 *  9. 아이템 클릭 → 저장된 기본 플레이어로 직접 실행
 * 10. 별점 영역 탭 → 별점 입력 팝업 → 파일명 기준 저장
 * 11. 롱클릭 → 편집하기/파일명 변경/삭제 액션 시트 (별점과 완전히 분리된 동작)
 * 12. 1080p 초과 영상은 FFmpeg로 1080p/H.265/AAC 압축 후 가져오기
 * 13. 재생 시도한 영상은 "최근 재생"으로 기록되어 목록에서 강조 표시
 */
class MainActivity : AppCompatActivity() {

    // --- View -----------------------------------------------------------------
    private lateinit var recyclerView: RecyclerView
    private lateinit var btnShuffle: Button
    private lateinit var btnSortRating: Button
    private lateinit var btnSortDate: Button
    private lateinit var btnPlayerSetting: TextView
    private lateinit var editSelectionStrip: View
    private lateinit var tvEditSelectionMessage: TextView
    private lateinit var btnCancelEditSelection: Button
    private lateinit var mainTabs: TabLayout
    private lateinit var mainPager: ViewPager2
    private lateinit var downloadStatusStrip: View
    private lateinit var tvDownloadSummary: TextView
    private lateinit var tvDownloadTitle: TextView
    private lateinit var downloadStatusProgress: ProgressBar
    private lateinit var progressBar: ProgressBar
    private lateinit var tvEmpty: TextView

    // --- Data & Adapter -------------------------------------------------------
    private val videoList    = mutableListOf<VideoItem>()
    private val allVideoList = mutableListOf<VideoItem>()
    private var currentFilter: RatingFilter = RatingFilter.ALL
    private var currentSortMode: VideoSortMode = VideoSortMode.NEWEST_FIRST
    private var selectionAction: VideoSelectionAction? = null
    private lateinit var adapter: VideoAdapter

    // --- Coroutine ------------------------------------------------------------
    private val scope = CoroutineScope(Dispatchers.Main + SupervisorJob())
    private var activeFfmpegSessionId: Long? = null
    private var mediaTransformer: Transformer? = null
    private var currentImportTempFile: File? = null
    private var isUnlocked = false
    private var stopDownloadStatusListening: (() -> Unit)? = null
    private var browserController: BrowserWebViewController? = null
    private var downloadController: DownloadStatusController? = null
    private val networkGate: NetworkConnectivityGate by lazy { NetworkConnectivityGate(applicationContext) }
    private var networkCallback: ConnectivityManager.NetworkCallback? = null
    private var importChangedReceiverRegistered = false
    private val importChangedReceiver = object : BroadcastReceiver() {
        override fun onReceive(context: Context?, intent: Intent?) {
            if (
                (intent?.action == VideoImportService.ACTION_IMPORT_CHANGED ||
                    intent?.action == VideoTrimService.ACTION_TRIM_CHANGED) &&
                isUnlocked
            ) {
                loadVideos()
            }
        }
    }

    private val pickVideoLauncher = registerForActivityResult(ActivityResultContracts.OpenMultipleDocuments()) { uris ->
        if (uris.isNotEmpty()) {
            uris.forEach(::persistImportReadPermission)
            showImportOptions(uris)
        }
    }

    // --- Lifecycle ------------------------------------------------------------

    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        checkNetworkThenForceUpdate()
    }

    private fun checkNetworkThenForceUpdate() {
        if (networkGate.isConnected()) {
            checkForceUpdate()
            return
        }
        val dialog = MaterialAlertDialogBuilder(this)
            .setTitle("인터넷 연결 필요")
            .setMessage("이 앱은 인터넷 연결이 필요합니다. 연결하면 자동으로 진행됩니다.")
            .setCancelable(false)
            .show()
        networkCallback = networkGate.awaitConnectivity {
            runOnUiThread {
                dialog.dismiss()
                networkCallback?.let { networkGate.stopAwaiting(it) }
                networkCallback = null
                checkForceUpdate()
            }
        }
    }

    private fun checkForceUpdate() {
        scope.launch {
            val result = ForceUpdateGate(applicationContext).check(BuildConfig.VERSION_CODE)
            runWhenStarted {
                if (result.decision == ForceUpdateDecision.BLOCK) {
                    showForceUpdateDialog(result)
                } else {
                    authenticateBeforeOpening()
                }
            }
        }
    }

    private fun runWhenStarted(action: () -> Unit) {
        if (lifecycle.currentState.isAtLeast(Lifecycle.State.STARTED)) {
            action()
            return
        }
        lifecycle.addObserver(object : LifecycleEventObserver {
            override fun onStateChanged(source: LifecycleOwner, event: Lifecycle.Event) {
                when (event) {
                    Lifecycle.Event.ON_START -> {
                        lifecycle.removeObserver(this)
                        action()
                    }
                    Lifecycle.Event.ON_DESTROY -> lifecycle.removeObserver(this)
                    else -> Unit
                }
            }
        })
    }

    private fun showForceUpdateDialog(result: ForceUpdateResult) {
        MaterialAlertDialogBuilder(this)
            .setTitle("업데이트 필요")
            .setMessage(result.message)
            .setCancelable(false)
            .setPositiveButton("업데이트") { _, _ ->
                try {
                    startActivity(Intent(Intent.ACTION_VIEW, Uri.parse(result.updateUrl)))
                } catch (e: Exception) {
                    Toast.makeText(
                        this,
                        "스토어를 열 수 없습니다: ${e.message ?: e.javaClass.simpleName}",
                        Toast.LENGTH_SHORT
                    ).show()
                }
                finish()
            }
            .show()
    }

    private fun openUnlockedApp() {
        if (isUnlocked) return
        isUnlocked = true
        setContentView(R.layout.activity_main)

        VideoPreferenceManager.init(this)
        RatingBackupManager.init(this)
        BrowserPreferenceManager.init(this)
        HlsDownloadStore.initialize(applicationContext)
        requestAllFilesAccessIfNeeded()
        requestNotificationPermissionIfNeeded()
        initViews()
        registerImportChangedReceiver()
        beginDownloadStatusListening()

        scope.launch {
            val restored = RatingBackupManager.restoreIfLocalEmpty()
            if (restored) {
                Toast.makeText(this@MainActivity, "이전 데이터를 백업에서 복원했습니다.", Toast.LENGTH_SHORT).show()
            }
            loadVideos()
        }
    }

    override fun onDestroy() {
        super.onDestroy()
        activeFfmpegSessionId?.let(FFmpegKit::cancel)
        mediaTransformer?.cancel()
        currentImportTempFile?.delete()
        stopDownloadStatusListening?.invoke()
        stopDownloadStatusListening = null
        browserController?.destroy()
        downloadController?.destroy()
        networkCallback?.let { networkGate.stopAwaiting(it) }
        scope.cancel()
    }

    override fun onStart() {
        super.onStart()
        if (isUnlocked && ::downloadStatusStrip.isInitialized) {
            registerImportChangedReceiver()
            beginDownloadStatusListening()
            downloadController?.resume()
        }
    }

    override fun onStop() {
        unregisterImportChangedReceiver()
        stopDownloadStatusListening?.invoke()
        stopDownloadStatusListening = null
        downloadController?.pause()
        super.onStop()
    }

    private fun registerImportChangedReceiver() {
        if (importChangedReceiverRegistered) return
        val intentFilter = IntentFilter(VideoImportService.ACTION_IMPORT_CHANGED).apply {
            addAction(VideoTrimService.ACTION_TRIM_CHANGED)
        }
        ContextCompat.registerReceiver(
            this,
            importChangedReceiver,
            intentFilter,
            ContextCompat.RECEIVER_NOT_EXPORTED
        )
        importChangedReceiverRegistered = true
    }

    private fun unregisterImportChangedReceiver() {
        if (!importChangedReceiverRegistered) return
        runCatching { unregisterReceiver(importChangedReceiver) }
        importChangedReceiverRegistered = false
    }

    // --- 초기화 ----------------------------------------------------------------

    private fun initViews() {
        btnPlayerSetting = findViewById(R.id.btn_player_setting)
        mainTabs         = findViewById(R.id.main_tabs)
        mainPager        = findViewById(R.id.main_pager)

        findViewById<TextView>(R.id.tv_main_title).text = MainScreenUiModel.title

        val inflater = LayoutInflater.from(this)
        val browserPage = inflater.inflate(R.layout.page_browser, mainPager, false)
        val videoPage = inflater.inflate(R.layout.page_video_library, mainPager, false)
        val downloadPage = inflater.inflate(R.layout.page_download_status, mainPager, false)
        setupMainPager(listOf(browserPage, videoPage, downloadPage))

        progressBar      = videoPage.findViewById(R.id.progress_bar)
        tvEmpty          = videoPage.findViewById(R.id.tv_empty)
        btnShuffle       = videoPage.findViewById(R.id.btn_shuffle)
        btnSortRating    = videoPage.findViewById(R.id.btn_sort_rating)
        btnSortDate      = videoPage.findViewById(R.id.btn_sort_date)
        editSelectionStrip = videoPage.findViewById(R.id.edit_selection_strip)
        tvEditSelectionMessage = videoPage.findViewById(R.id.tv_edit_selection_message)
        btnCancelEditSelection = videoPage.findViewById(R.id.btn_cancel_edit_selection)
        downloadStatusStrip = videoPage.findViewById(R.id.download_status_strip)
        tvDownloadSummary = videoPage.findViewById(R.id.tv_download_summary)
        tvDownloadTitle = videoPage.findViewById(R.id.tv_download_title)
        downloadStatusProgress = videoPage.findViewById(R.id.download_status_progress)
        recyclerView     = videoPage.findViewById(R.id.recycler_view)

        browserController = BrowserWebViewController(
            activity = this,
            root = browserPage,
            onOpenDownloads = { mainPager.currentItem = MainScreenUiModel.downloadPageIndex }
        ).also { it.start() }
        downloadController = DownloadStatusController(
            activity = this,
            root = downloadPage,
            onClose = { mainPager.currentItem = MainScreenUiModel.defaultPageIndex },
            onImportRequested = { path ->
                showImportOptions(listOf(Uri.fromFile(File(path))), deleteSourceAfterImport = false)
            }
        ).also {
            it.start()
            it.resume()
        }
        onBackPressedDispatcher.addCallback(this, object : OnBackPressedCallback(true) {
            override fun handleOnBackPressed() {
                if (selectionAction != null) {
                    setVideoSelectionAction(null)
                } else if (mainPager.currentItem == MainScreenUiModel.browserPageIndex && browserController?.handleBack() == true) {
                    return
                } else if (mainPager.currentItem != MainScreenUiModel.defaultPageIndex) {
                    mainPager.currentItem = MainScreenUiModel.defaultPageIndex
                } else {
                    isEnabled = false
                    onBackPressedDispatcher.onBackPressed()
                }
            }
        })

        adapter = VideoAdapter(
            context         = this,
            videoList       = videoList,
            onItemClick     = { video ->
                when (selectionAction) {
                    VideoSelectionAction.TRIM -> showTrimDialog(video)
                    VideoSelectionAction.RENAME -> showRenameDialog(video)
                    null -> openVideoPlayer(video)
                }
            },
            onRatingChanged = { video, rating ->
                VideoPreferenceManager.saveRating(video.ratingPreferenceKey(), rating)
                RatingBackupManager.scheduleExport()
                applyCurrentListState()
            },
            onItemLongPress = { video -> showVideoActionSheet(video) }
        )
        recyclerView.layoutManager = LinearLayoutManager(this)
        recyclerView.adapter = adapter
        adapter.setLastPlayedPath(VideoPreferenceManager.getLastPlayedPath())

        btnShuffle.setOnClickListener {
            if (allVideoList.isNotEmpty()) {
                allVideoList.shuffle()
                currentSortMode = VideoSortMode.RANDOM
                adapter.updateList(filterVideos(allVideoList, currentFilter))
                updateSortButtons()
                updateEmptyState()
            }
        }

        btnSortRating.setOnClickListener {
            showRatingFilterDialog()
        }

        btnPlayerSetting.setOnClickListener {
            showPlayerSettingMenu()
        }

        btnSortDate.setOnClickListener {
            showDateSortDialog()
        }

        downloadStatusStrip.setOnClickListener {
            mainPager.currentItem = MainScreenUiModel.downloadPageIndex
        }

        btnCancelEditSelection.setOnClickListener {
            setVideoSelectionAction(null)
        }

        updateSortButtons()
    }

    private fun setupMainPager(pages: List<View>) {
        mainPager.adapter = MainPagerAdapter(pages)
        mainPager.offscreenPageLimit = MainScreenUiModel.pageCount - 1
        mainPager.isUserInputEnabled = false
        TabLayoutMediator(mainTabs, mainPager) { tab, position ->
            tab.text = MainScreenUiModel.tabTitle(position)
        }.attach()
        mainPager.setCurrentItem(MainScreenUiModel.defaultPageIndex, false)
    }

    private fun beginDownloadStatusListening() {
        stopDownloadStatusListening?.invoke()
        stopDownloadStatusListening = HlsDownloadStore.listen { progresses ->
            runOnUiThread { renderDownloadStatus(progresses) }
        }
    }

    private fun renderDownloadStatus(progresses: List<HlsDownloadProgress>) {
        val summary = MainScreenUiModel.downloadSummary(progresses)
        val active = MainScreenUiModel.activeDownload(progresses)
        downloadStatusStrip.visibility = if (summary == null || active == null) View.GONE else View.VISIBLE
        if (summary == null || active == null) return
        tvDownloadSummary.text = summary
        tvDownloadTitle.text = active.title.ifBlank { "동영상" }
        downloadStatusProgress.progress = active.percent
    }

    // --- 권한 처리 ------------------------------------------------------------

    /**
     * API 30+에서 별점/설정 백업 파일을 재설치 후에도 안정적으로 읽으려면
     * MANAGE_EXTERNAL_STORAGE("모든 파일 액세스 관리")가 필요하다.
     * 일반 런타임 권한 다이얼로그로는 요청할 수 없어 설정 화면으로 안내한다.
     * (영상 자체는 앱 전용 저장소를 쓰므로 이 권한과 무관하게 항상 접근 가능하다.)
     */
    private fun requestAllFilesAccessIfNeeded() {
        if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.R && !Environment.isExternalStorageManager()) {
            try {
                val intent = Intent(Settings.ACTION_MANAGE_APP_ALL_FILES_ACCESS_PERMISSION).apply {
                    data = Uri.parse("package:$packageName")
                }
                startActivity(intent)
            } catch (e: Exception) {
                Toast.makeText(this, "별점 백업을 위해 설정 > 앱 > 모든 파일 액세스 권한을 허용해 주세요.", Toast.LENGTH_LONG).show()
            }
        }
    }

    private fun requestNotificationPermissionIfNeeded() {
        if (Build.VERSION.SDK_INT < Build.VERSION_CODES.TIRAMISU) return
        if (ContextCompat.checkSelfPermission(this, Manifest.permission.POST_NOTIFICATIONS) == PackageManager.PERMISSION_GRANTED) return
        requestPermissions(arrayOf(Manifest.permission.POST_NOTIFICATIONS), REQUEST_POST_NOTIFICATIONS)
    }

    // --- 잠금 해제 -------------------------------------------------------------

    private fun authenticateBeforeOpening() {
        val biometricManager = BiometricManager.from(this)
        if (biometricManager.canAuthenticate(BIOMETRIC_AUTHENTICATORS) != BiometricManager.BIOMETRIC_SUCCESS) {
            Toast.makeText(this, "지문 인증을 사용할 수 없어 앱을 열 수 없습니다.", Toast.LENGTH_LONG).show()
            finish()
            return
        }

        val prompt = BiometricPrompt(
            this,
            ContextCompat.getMainExecutor(this),
            object : BiometricPrompt.AuthenticationCallback() {
                override fun onAuthenticationSucceeded(result: BiometricPrompt.AuthenticationResult) {
                    openUnlockedApp()
                }

                override fun onAuthenticationError(errorCode: Int, errString: CharSequence) {
                    Toast.makeText(this@MainActivity, errString.toString(), Toast.LENGTH_SHORT).show()
                    finish()
                }
            }
        )

        val promptInfo = BiometricPrompt.PromptInfo.Builder()
            .setTitle("Meet 잠금 해제")
            .setSubtitle("지문으로 앱을 여세요.")
            .setAllowedAuthenticators(BIOMETRIC_AUTHENTICATORS)
            .setNegativeButtonText("취소")
            .build()

        prompt.authenticate(promptInfo)
    }

    // --- 영상 로딩 -------------------------------------------------------------

    /** 영상을 담아두는 앱 전용 폴더. 갤러리/파일 앱에 노출되지 않으며, 여기에 직접 파일을 넣어야 한다. */
    private fun videosDir(): File =
        File(getExternalFilesDir(null), HlsDownloadOutputPolicy.libraryDirectoryName).apply { if (!exists()) mkdirs() }

    private fun loadVideos() {
        scope.launch {
            showLoading(true)
            val result = withContext(Dispatchers.IO) { queryVideosFromAppStorage() }
            allVideoList.clear()
            allVideoList.addAll(result)
            currentFilter = VideoPreferenceManager.getRatingFilter()
            currentSortMode = VideoSortMode.NEWEST_FIRST
            applyCurrentListState()
            VideoThumbnailCache.prune(applicationContext)
            showLoading(false)
            updateEmptyState()
        }
    }

    private val videoExtensions = setOf("mp4", "mkv", "avi", "mov", "webm", "3gp", "m4v", "ts")

    private fun queryVideosFromAppStorage(): List<VideoItem> {
        val files = videosDir().listFiles { file ->
            file.isFile && file.extension.lowercase() in videoExtensions
        } ?: emptyArray()

        return files.map { file ->
            VideoItem(
                name         = file.name,
                path         = file.absolutePath,
                duration     = extractDurationMs(file),
                size         = file.length(),
                dateModified = file.lastModified() / 1000,
                rating       = loadRatingFor(file)
            )
        }
    }

    private fun loadRatingFor(file: File): Float {
        val byName = VideoPreferenceManager.getRating(file.name)
        return if (byName != 0f) byName else VideoPreferenceManager.getRating(file.absolutePath)
    }

    private fun extractDurationMs(file: File): Long {
        val retriever = MediaMetadataRetriever()
        return try {
            retriever.setDataSource(file.absolutePath)
            retriever.extractMetadata(MediaMetadataRetriever.METADATA_KEY_DURATION)?.toLongOrNull() ?: 0L
        } catch (e: Exception) {
            0L
        } finally {
            try { retriever.release() } catch (_: Exception) {}
        }
    }

    // --- 영상 가져오기 ---------------------------------------------------------

    private fun showImportOptions(uris: List<Uri>, deleteSourceAfterImport: Boolean = true) {
        scope.launch {
            showLoading(true)
            val metadataList = withContext(Dispatchers.IO) {
                uris.map { uri -> ImportVideoSelection(uri, readImportMetadata(uri)) }
            }
            showLoading(false)

            var compressSelected = true
            var selectedBitrate = VideoImportOption.DEFAULT_BITRATE
            val content = LinearLayout(this@MainActivity).apply {
                orientation = LinearLayout.VERTICAL
                val padding = (20 * resources.displayMetrics.density).toInt()
                setPadding(padding)
            }

            lateinit var originalButton: RadioButton
            lateinit var compressButton: RadioButton
            lateinit var bitrateContainer: LinearLayout
            val optionContainer = LinearLayout(this@MainActivity).apply {
                orientation = LinearLayout.VERTICAL
            }
            val summary = TextView(this@MainActivity).apply {
                textSize = 14f
                setTextColor(0xFF263238.toInt())
                layoutParams = LinearLayout.LayoutParams(
                    LinearLayout.LayoutParams.MATCH_PARENT,
                    LinearLayout.LayoutParams.WRAP_CONTENT
                ).apply {
                    topMargin = dp(12)
                }
            }
            val listContainer = LinearLayout(this@MainActivity).apply {
                orientation = LinearLayout.VERTICAL
            }
            val scrollView = ScrollView(this@MainActivity).apply {
                addView(listContainer)
                layoutParams = LinearLayout.LayoutParams(
                    LinearLayout.LayoutParams.MATCH_PARENT,
                    LinearLayout.LayoutParams.WRAP_CONTENT
                )
            }

            fun refreshPreview() {
                originalButton.isChecked = !compressSelected
                compressButton.isChecked = compressSelected
                bitrateContainer.visibility = if (compressSelected) View.VISIBLE else View.GONE
                val option = if (compressSelected) {
                    VideoImportOption.compress(selectedBitrate)
                } else {
                    VideoImportOption.original
                }
                summary.text = if (compressSelected) {
                    "1080p 초과 또는 ${formatMbps(selectedBitrate)}보다 큰 영상만 압축합니다."
                } else {
                    VideoImportOption.original.description
                }
                listContainer.removeAllViews()
                metadataList.forEach { selection ->
                    val preview = VideoImportPreview.create(
                        name = selection.metadata.title,
                        width = selection.metadata.width,
                        height = selection.metadata.height,
                        bitrate = selection.metadata.bitrate,
                        sizeBytes = selection.metadata.sizeBytes,
                        durationMs = selection.metadata.durationMs,
                        codecMime = selection.metadata.codecMime,
                        option = option
                    )
                    listContainer.addView(createPreviewRow(preview, selection.metadata.thumbnail))
                }
            }

            createDialogChoiceRow(
                label = "원본",
                checked = !compressSelected
            ) {
                compressSelected = false
                refreshPreview()
            }.also { row ->
                originalButton = row.getChildAt(0) as RadioButton
                optionContainer.addView(row)
            }

            createDialogChoiceRow(
                label = "압축",
                checked = compressSelected
            ) {
                compressSelected = true
                refreshPreview()
            }.also { row ->
                compressButton = row.getChildAt(0) as RadioButton
                optionContainer.addView(row)
            }

            val bitrateValue = TextView(this@MainActivity).apply {
                text = formatMbps(selectedBitrate)
                textSize = 16f
                setTextColor(ContextCompat.getColor(this@MainActivity, R.color.text_primary))
                setTypeface(typeface, android.graphics.Typeface.BOLD)
                gravity = Gravity.END
            }
            bitrateContainer = LinearLayout(this@MainActivity).apply {
                orientation = LinearLayout.VERTICAL
                setPadding(dp(8), dp(10), dp(8), dp(2))
                addView(LinearLayout(this@MainActivity).apply {
                    orientation = LinearLayout.HORIZONTAL
                    gravity = Gravity.CENTER_VERTICAL
                    addView(TextView(this@MainActivity).apply {
                        text = "비트레이트"
                        textSize = 13f
                        setTextColor(ContextCompat.getColor(this@MainActivity, R.color.text_secondary))
                        layoutParams = LinearLayout.LayoutParams(0, LinearLayout.LayoutParams.WRAP_CONTENT, 1f)
                    })
                    addView(bitrateValue)
                })
                addView(Slider(this@MainActivity).apply {
                    valueFrom = VideoImportOption.MIN_BITRATE / 1_000_000f
                    valueTo = VideoImportOption.MAX_BITRATE / 1_000_000f
                    stepSize = 0.1f
                    value = selectedBitrate / 1_000_000f
                    addOnChangeListener { _, value, _ ->
                        selectedBitrate = (value * 1_000_000).toInt()
                        bitrateValue.text = formatMbps(selectedBitrate)
                        refreshPreview()
                    }
                })
            }

            content.addView(optionContainer)
            content.addView(bitrateContainer)
            content.addView(summary)
            content.addView(scrollView)
            refreshPreview()

            MaterialAlertDialogBuilder(this@MainActivity)
                .setTitle("가져오기 옵션")
                .setView(content)
                .setPositiveButton("가져오기") { _, _ ->
                    val option = if (compressSelected) {
                        VideoImportOption.compress(selectedBitrate)
                    } else {
                        VideoImportOption.original
                    }
                    importSelectedVideos(metadataList, option, deleteSourceAfterImport)
                }
                .setNegativeButton("취소", null)
                .show()
        }
    }

    private fun createPreviewRow(preview: VideoImportPreview, thumbnail: Bitmap?): View {
        val density = resources.displayMetrics.density
        val thumbnailSize = (56 * density).toInt()

        val thumbnailView = ImageView(this).apply {
            scaleType = ImageView.ScaleType.CENTER_CROP
            layoutParams = LinearLayout.LayoutParams(thumbnailSize, thumbnailSize).apply {
                marginEnd = (10 * density).toInt()
            }
        }
        val requestOptions = RequestOptions().transform(CenterCrop(), RoundedCorners(8))
        if (thumbnail != null) {
            Glide.with(applicationContext)
                .load(thumbnail)
                .apply(requestOptions)
                .placeholder(R.drawable.ic_video_placeholder)
                .into(thumbnailView)
        } else {
            thumbnailView.setImageResource(R.drawable.ic_video_placeholder)
        }

        val textColumn = LinearLayout(this).apply {
            orientation = LinearLayout.VERTICAL
            layoutParams = LinearLayout.LayoutParams(0, LinearLayout.LayoutParams.WRAP_CONTENT, 1f)
        }
        textColumn.addView(TextView(this).apply {
            text = preview.name
            textSize = 14f
            setTextColor(0xFF111827.toInt())
        })
        textColumn.addView(TextView(this).apply {
            text = buildPreviewDetail(preview)
            textSize = 12f
            setTextColor(0xFF546E7A.toInt())
        })
        textColumn.addView(LinearLayout(this).apply {
            orientation = LinearLayout.HORIZONTAL
            addView(createBadge(preview.qualityStatus.label, preview.qualityStatus.color))
            addView(createBadge(preview.actionLabel, preview.actionColor))
        })

        val row = LinearLayout(this).apply {
            orientation = LinearLayout.HORIZONTAL
            setPadding((10 * density).toInt(), (10 * density).toInt(), (10 * density).toInt(), (8 * density).toInt())
        }
        row.addView(thumbnailView)
        row.addView(textColumn)
        return row
    }

    private fun createBadge(label: String, color: Int): TextView =
        TextView(this).apply {
            text = label
            textSize = 12f
            setTextColor(0xFFFFFFFF.toInt())
            setBackgroundColor(color)
            val padX = (8 * resources.displayMetrics.density).toInt()
            val padY = (4 * resources.displayMetrics.density).toInt()
            setPadding(padX, padY, padX, padY)
            layoutParams = LinearLayout.LayoutParams(
                LinearLayout.LayoutParams.WRAP_CONTENT,
                LinearLayout.LayoutParams.WRAP_CONTENT
            ).apply {
                topMargin = (6 * resources.displayMetrics.density).toInt()
                rightMargin = (6 * resources.displayMetrics.density).toInt()
            }
        }

    private fun buildPreviewDetail(preview: VideoImportPreview): String {
        val resolution = preview.height?.let { "${it}p" } ?: "해상도 정보 없음"
        val bitrate = preview.bitrate?.let { "${String.format("%.1f", it / 1_000_000f)}Mbps" } ?: "비트레이트 정보 없음"
        val size = preview.sizeBytes?.takeIf { it >= 0L }?.let { Formatter.formatFileSize(this, it) } ?: "용량 정보 없음"
        val estimate = preview.estimatedOutputSizeBytes
            ?.takeIf { preview.policy.shouldCompress }
            ?.let { "예상 ${Formatter.formatFileSize(this, it)}" }
            ?: if (preview.policy.shouldCompress) "예상 용량 계산 불가" else "원본 유지"
        return "$resolution · ${preview.codecLabel} · $bitrate\n원본 $size · $estimate"
    }

    private data class ImportProgressUi(
        val dialog: AlertDialog,
        val title: TextView,
        val detail: TextView,
        val progressBar: ProgressBar,
        val percent: TextView
    )

    private fun showImportProgressDialog(totalFiles: Int, onCancelImport: () -> Unit): ImportProgressUi {
        val content = LinearLayout(this).apply {
            orientation = LinearLayout.VERTICAL
            setPadding(dp(24), dp(18), dp(24), dp(8))
        }
        val title = TextView(this).apply {
            text = "가져오기 준비 중"
            textSize = 18f
            setTextColor(ContextCompat.getColor(this@MainActivity, R.color.text_primary))
            setTypeface(typeface, android.graphics.Typeface.BOLD)
        }
        val detail = TextView(this).apply {
            text = "총 ${totalFiles}개 파일"
            textSize = 13f
            setTextColor(ContextCompat.getColor(this@MainActivity, R.color.text_secondary))
            layoutParams = LinearLayout.LayoutParams(
                LinearLayout.LayoutParams.MATCH_PARENT,
                LinearLayout.LayoutParams.WRAP_CONTENT
            ).apply { topMargin = dp(8) }
        }
        val progressBar = ProgressBar(this, null, android.R.attr.progressBarStyleHorizontal).apply {
            max = 100
            progress = 0
            progressTintList = ColorStateList.valueOf(ContextCompat.getColor(this@MainActivity, R.color.color_accent))
            progressBackgroundTintList = ColorStateList.valueOf(ContextCompat.getColor(this@MainActivity, R.color.divider_soft))
            layoutParams = LinearLayout.LayoutParams(
                LinearLayout.LayoutParams.MATCH_PARENT,
                dp(8)
            ).apply { topMargin = dp(18) }
        }
        val percent = TextView(this).apply {
            text = "0%"
            gravity = Gravity.END
            textSize = 13f
            setTextColor(ContextCompat.getColor(this@MainActivity, R.color.text_secondary))
            layoutParams = LinearLayout.LayoutParams(
                LinearLayout.LayoutParams.MATCH_PARENT,
                LinearLayout.LayoutParams.WRAP_CONTENT
            ).apply { topMargin = dp(8) }
        }

        content.addView(title)
        content.addView(detail)
        content.addView(progressBar)
        content.addView(percent)

        val dialog = MaterialAlertDialogBuilder(this)
            .setView(content)
            .setNegativeButton("가져오기 취소", null)
            .create()
        dialog.setCancelable(false)
        dialog.show()
        dialog.getButton(AlertDialog.BUTTON_NEGATIVE).setOnClickListener {
            it.isEnabled = false
            title.text = "가져오기 취소 중"
            onCancelImport()
        }

        return ImportProgressUi(dialog, title, detail, progressBar, percent)
    }

    private fun updateImportProgress(
        progressUi: ImportProgressUi,
        fileIndex: Int,
        totalFiles: Int,
        fileName: String,
        action: String,
        fileProgress: Int
    ) {
        val boundedFileProgress = fileProgress.coerceIn(0, 100)
        val totalProgress = (((fileIndex * 100) + boundedFileProgress) / totalFiles).coerceIn(0, 100)
        progressUi.title.text = "$action (${fileIndex + 1}/$totalFiles)"
        progressUi.detail.text = fileName
        progressUi.progressBar.progress = totalProgress
        progressUi.percent.text = "$totalProgress%"
    }

    private fun formatMbps(bitrate: Int): String =
        "${String.format("%.1f", bitrate / 1_000_000f)} Mbps"

    private fun importSelectedVideos(
        selections: List<ImportVideoSelection>,
        option: VideoImportOption,
        deleteSourceAfterImport: Boolean
    ) {
        val request = VideoImportRequest(
            option = option,
            items = selections.map { selection ->
                VideoImportItem(
                    uri = selection.uri.toString(),
                    title = selection.metadata.title,
                    sizeBytes = selection.metadata.sizeBytes,
                    width = selection.metadata.width,
                    height = selection.metadata.height,
                    bitrate = selection.metadata.bitrate,
                    durationMs = selection.metadata.durationMs,
                    codecMime = selection.metadata.codecMime
                )
            },
            deleteSourceAfterImport = deleteSourceAfterImport
        )
        VideoImportService.start(this, request)
        Toast.makeText(this, "가져오기를 백그라운드에서 시작했습니다. 알림에서 진행률을 확인하세요.", Toast.LENGTH_LONG).show()
    }

    private fun persistImportReadPermission(uri: Uri) {
        runCatching {
            contentResolver.takePersistableUriPermission(uri, Intent.FLAG_GRANT_READ_URI_PERMISSION)
        }
    }

    private fun deleteOriginalSource(uri: Uri): Boolean =
        when (uri.scheme) {
            "content" -> tryDeleteDocument(uri) || tryDeleteContentUri(uri)
            "file" -> uri.path?.let { path -> runCatching { File(path).delete() }.getOrDefault(false) } == true
            else -> false
        }

    private fun tryDeleteDocument(uri: Uri): Boolean =
        runCatching { DocumentsContract.deleteDocument(contentResolver, uri) }.getOrDefault(false)

    private fun tryDeleteContentUri(uri: Uri): Boolean =
        runCatching { contentResolver.delete(uri, null, null) > 0 }.getOrDefault(false)

    private fun readImportMetadata(uri: Uri): ImportVideoMetadata {
        val retriever = MediaMetadataRetriever()
        val displayName = readDisplayName(uri)
        val mediaStoreName = readMediaStoreName(uri)
        return try {
            retriever.setDataSource(this, uri)
            val durationMs = retriever.extractMetadata(MediaMetadataRetriever.METADATA_KEY_DURATION)?.toLongOrNull()
            ImportVideoMetadata(
                title = VideoImportFileName.choose(
                    displayName = displayName,
                    mediaStoreName = mediaStoreName,
                    fallbackSegment = uri.lastPathSegment
                ),
                sizeBytes = readOpenableSize(uri),
                width = retriever.extractMetadata(MediaMetadataRetriever.METADATA_KEY_VIDEO_WIDTH)?.toIntOrNull(),
                height = retriever.extractMetadata(MediaMetadataRetriever.METADATA_KEY_VIDEO_HEIGHT)?.toIntOrNull(),
                bitrate = retriever.extractMetadata(MediaMetadataRetriever.METADATA_KEY_BITRATE)?.toIntOrNull(),
                durationMs = durationMs,
                codecMime = readVideoCodecMime(uri),
                thumbnail = extractImportThumbnail(retriever, durationMs)
            )
        } catch (_: RuntimeException) {
            ImportVideoMetadata(
                title = VideoImportFileName.choose(
                    displayName = displayName,
                    mediaStoreName = mediaStoreName,
                    fallbackSegment = uri.lastPathSegment
                ),
                sizeBytes = readOpenableSize(uri)
            )
        } finally {
            retriever.release()
        }
    }

    /** 컨테이너 안의 첫 비디오 트랙 mime 타입(H.264/H.265 등)을 읽는다. 실패하면 null. */
    private fun readVideoCodecMime(uri: Uri): String? {
        val extractor = MediaExtractor()
        return try {
            extractor.setDataSource(this, uri, null)
            (0 until extractor.trackCount)
                .asSequence()
                .map { extractor.getTrackFormat(it) }
                .mapNotNull { format -> format.getString(MediaFormat.KEY_MIME) }
                .firstOrNull { mime -> mime.startsWith("video/") }
        } catch (_: Exception) {
            null
        } finally {
            extractor.release()
        }
    }

    /** 검은 첫 프레임을 피해 대표 프레임을 추출한다. VideoAdapter.extractThumbnail 과 동일한 탐색 시점 규칙. */
    private fun extractImportThumbnail(retriever: MediaMetadataRetriever, durationMs: Long?): Bitmap? {
        val duration = durationMs?.takeIf { it > 0L } ?: 0L
        val seekTimeUs = when {
            duration <= 0L -> 0L
            duration < 2_000L -> duration * 1_000L / 2
            else -> minOf(1_000_000L, duration * 1_000L / 10)
        }
        return try {
            retriever.getFrameAtTime(seekTimeUs, MediaMetadataRetriever.OPTION_CLOSEST_SYNC)
        } catch (_: Exception) {
            null
        }
    }

    private fun readDisplayName(uri: Uri): String? =
        contentResolver.query(
            uri,
            arrayOf(android.provider.OpenableColumns.DISPLAY_NAME),
            null,
            null,
            null
        )?.use { cursor ->
            if (!cursor.moveToFirst()) return@use null
            val index = cursor.getColumnIndex(android.provider.OpenableColumns.DISPLAY_NAME)
            if (index >= 0 && !cursor.isNull(index)) cursor.getString(index) else null
        }

    private fun readMediaStoreName(uri: Uri): String? =
        runCatching {
            contentResolver.query(
                uri,
                arrayOf(android.provider.MediaStore.Video.Media.DISPLAY_NAME),
                null,
                null,
                null
            )?.use { cursor ->
                if (!cursor.moveToFirst()) return@use null
                val index = cursor.getColumnIndex(android.provider.MediaStore.Video.Media.DISPLAY_NAME)
                if (index >= 0 && !cursor.isNull(index)) cursor.getString(index) else null
            }
        }.getOrNull()

    private fun readOpenableSize(uri: Uri): Long? =
        contentResolver.query(
            uri,
            arrayOf(android.provider.OpenableColumns.SIZE),
            null,
            null,
            null
        )?.use { cursor ->
            if (!cursor.moveToFirst()) return@use null
            val index = cursor.getColumnIndex(android.provider.OpenableColumns.SIZE)
            if (index >= 0 && !cursor.isNull(index)) cursor.getLong(index) else null
        }

    private suspend fun copySelectedVideo(
        uri: Uri,
        metadata: ImportVideoMetadata,
        onProgress: (Int) -> Unit
    ): File {
        val outputFile = uniqueVideoFile(metadata.title)
        return try {
            withContext(Dispatchers.IO) {
                contentResolver.openInputStream(uri)?.use { input ->
                    outputFile.outputStream().use { output ->
                        val totalBytes = metadata.sizeBytes?.takeIf { it > 0L }
                        val buffer = ByteArray(DEFAULT_BUFFER_SIZE)
                        var copiedBytes = 0L
                        var lastProgress = -1
                        while (true) {
                            ensureActive()
                            val read = input.read(buffer)
                            if (read < 0) break
                            output.write(buffer, 0, read)
                            copiedBytes += read
                            val progress = totalBytes
                                ?.let { ((copiedBytes * 100L) / it).toInt().coerceIn(0, 99) }
                                ?: 50
                            if (progress != lastProgress) {
                                lastProgress = progress
                                withContext(Dispatchers.Main) { onProgress(progress) }
                            }
                        }
                        withContext(Dispatchers.Main) { onProgress(100) }
                    }
                } ?: error("선택한 파일을 열 수 없습니다.")
                outputFile
            }
        } catch (error: CancellationException) {
            outputFile.delete()
            throw error
        }
    }

    private suspend fun compressSelectedVideo(
        uri: Uri,
        metadata: ImportVideoMetadata,
        policy: VideoImportPolicy,
        onProgress: (Int) -> Unit
    ): File {
        val outputFile = uniqueVideoFile(VideoImportFileName.compressedOutputName(metadata.title))
        val inputTempFile = File(cacheDir, "import_input_${System.currentTimeMillis()}.${metadata.title.substringAfterLast('.', "mp4")}")
        currentImportTempFile = inputTempFile

        return try {
            copyUriToTempFile(uri, metadata, inputTempFile) { progress ->
                onProgress((progress * 5 / 100).coerceIn(0, 5))
            }
            executeFfmpegImportOrFallback(inputTempFile, outputFile, policy, metadata.durationMs) { progress ->
                onProgress((5 + (progress * 94 / 100)).coerceIn(5, 99))
            }
            onProgress(100)
            outputFile
        } catch (error: CancellationException) {
            outputFile.delete()
            throw error
        } finally {
            currentImportTempFile = null
            inputTempFile.delete()
        }
    }

    private suspend fun copyUriToTempFile(
        uri: Uri,
        metadata: ImportVideoMetadata,
        outputFile: File,
        onProgress: (Int) -> Unit
    ) {
        withContext(Dispatchers.IO) {
            contentResolver.openInputStream(uri)?.use { input ->
                outputFile.outputStream().use { output ->
                    val totalBytes = metadata.sizeBytes?.takeIf { it > 0L }
                    val buffer = ByteArray(DEFAULT_BUFFER_SIZE)
                    var copiedBytes = 0L
                    var lastProgress = -1
                    while (true) {
                        ensureActive()
                        val read = input.read(buffer)
                        if (read < 0) break
                        output.write(buffer, 0, read)
                        copiedBytes += read
                        val progress = totalBytes
                            ?.let { ((copiedBytes * 100L) / it).toInt().coerceIn(0, 99) }
                            ?: 50
                        if (progress != lastProgress) {
                            lastProgress = progress
                            withContext(Dispatchers.Main) { onProgress(progress) }
                        }
                    }
                }
            } ?: error("선택한 파일을 열 수 없습니다.")
        }
    }

    private suspend fun executeFfmpegImportOrFallback(
        inputFile: File,
        outputFile: File,
        policy: VideoImportPolicy,
        durationMs: Long?,
        onProgress: (Int) -> Unit
    ) {
        try {
            runFfmpegCommand(
                args = FfmpegImportCommand.hardware(inputFile.absolutePath, outputFile.absolutePath, policy),
                durationMs = durationMs,
                onProgress = onProgress
            ).recoverCatching { firstError ->
                outputFile.delete()
                runFfmpegCommand(
                    args = FfmpegImportCommand.softwareFallback(inputFile.absolutePath, outputFile.absolutePath, policy),
                    durationMs = durationMs,
                    onProgress = onProgress
                ).getOrElse { throw firstError }
            }.getOrThrow()
        } catch (error: Throwable) {
            if (error is CancellationException) throw error
            if (!FfmpegRuntimeAvailability.isUnavailable(error)) throw error
            outputFile.delete()
            exportVideoWithMedia3(
                inputUri = Uri.fromFile(inputFile),
                outputFile = outputFile,
                policy = policy,
                onProgress = onProgress
            )
        }
    }

    private suspend fun runFfmpegCommand(
        args: Array<String>,
        durationMs: Long?,
        onProgress: (Int) -> Unit
    ): Result<Unit> =
        suspendCancellableCoroutine { continuation ->
            val session = FFmpegKit.executeWithArgumentsAsync(
                args,
                { session ->
                    activeFfmpegSessionId = null
                    val returnCode = session.returnCode
                    when {
                        ReturnCode.isSuccess(returnCode) -> {
                            if (continuation.isActive) continuation.resume(Result.success(Unit))
                        }
                        ReturnCode.isCancel(returnCode) -> {
                            if (continuation.isActive) continuation.cancel()
                        }
                        else -> {
                            val message = session.failStackTrace ?: session.allLogsAsString ?: "FFmpeg 압축 실패"
                            if (continuation.isActive) continuation.resume(Result.failure(IllegalStateException(message)))
                        }
                    }
                },
                null,
                { statistics ->
                    val duration = durationMs?.takeIf { it > 0L } ?: return@executeWithArgumentsAsync
                    val progress = ((statistics.time * 100.0) / duration).toInt().coerceIn(0, 99)
                    onProgress(progress)
                }
            )
            activeFfmpegSessionId = session.sessionId
            continuation.invokeOnCancellation {
                activeFfmpegSessionId?.let(FFmpegKit::cancel)
                activeFfmpegSessionId = null
            }
        }

    private suspend fun exportVideoWithMedia3(
        inputUri: Uri,
        outputFile: File,
        policy: VideoImportPolicy,
        onProgress: (Int) -> Unit
    ) =
        suspendCancellableCoroutine<Unit> { continuation ->
            val editedMediaItem = EditedMediaItem.Builder(MediaItem.fromUri(inputUri))
                .setFrameRate(policy.targetFrameRate)
                .setEffects(
                    Effects(
                        emptyList<AudioProcessor>(),
                        listOf<Effect>(Presentation.createForHeight(policy.targetHeight))
                    )
                )
                .build()

            val encoderFactory = DefaultEncoderFactory.Builder(this)
                .setRequestedVideoEncoderSettings(
                    VideoEncoderSettings.Builder()
                        .setBitrate(policy.targetBitrate)
                        .build()
                )
                .setEnableFallback(true)
                .build()

            var progressJob: Job? = null
            mediaTransformer = Transformer.Builder(this)
                .setEncoderFactory(encoderFactory)
                .setVideoMimeType(MimeTypes.VIDEO_H265)
                .setAudioMimeType(MimeTypes.AUDIO_AAC)
                .addListener(
                    object : Transformer.Listener {
                        override fun onCompleted(composition: Composition, result: ExportResult) {
                            progressJob?.cancel()
                            onProgress(100)
                            mediaTransformer = null
                            if (continuation.isActive) continuation.resume(Unit)
                        }

                        override fun onError(
                            composition: Composition,
                            result: ExportResult,
                            exception: ExportException
                        ) {
                            progressJob?.cancel()
                            mediaTransformer = null
                            if (continuation.isActive) continuation.cancel(exception)
                        }
                    }
                )
                .build()

            continuation.invokeOnCancellation {
                progressJob?.cancel()
                mediaTransformer?.cancel()
                mediaTransformer = null
            }

            val activeTransformer = mediaTransformer
            progressJob = scope.launch {
                val holder = ProgressHolder()
                while (isActive && activeTransformer != null) {
                    val state = activeTransformer.getProgress(holder)
                    if (state == Transformer.PROGRESS_STATE_AVAILABLE) {
                        onProgress(holder.progress.coerceIn(0, 99))
                    }
                    delay(250)
                }
            }
            activeTransformer?.start(editedMediaItem, outputFile.absolutePath)
        }

    private fun uniqueVideoFile(fileName: String): File {
        val cleanName = fileName.ifBlank { "Meet_${System.currentTimeMillis()}.mp4" }
        val baseName = VideoFileNameSanitizer.sanitizeBaseName(cleanName.substringBeforeLast('.', cleanName))
        val extension = VideoFileNameSanitizer.sanitizeExtension(cleanName.substringAfterLast('.', "mp4"))
        var candidate = File(videosDir(), "$baseName.$extension")
        var index = 1
        while (candidate.exists()) {
            candidate = File(videosDir(), "${baseName}_$index.$extension")
            index++
        }
        return candidate
    }

    // --- 파일 삭제 -------------------------------------------------------------

    // --- 롱클릭 액션 시트 --------------------------------------------------------

    private fun showVideoActionSheet(video: VideoItem) {
        val dialog = BottomSheetDialog(this, R.style.ThemeOverlay_VideoManager_BottomSheet)
        val container = LinearLayout(this).apply {
            orientation = LinearLayout.VERTICAL
            setPadding(dp(8), dp(12), dp(8), dp(12))
        }

        container.addView(TextView(this).apply {
            text = video.name
            setTextColor(ContextCompat.getColor(this@MainActivity, R.color.text_secondary))
            textSize = 13f
            maxLines = 1
            ellipsize = TextUtils.TruncateAt.END
            setPadding(dp(10), 0, dp(10), dp(10))
        })
        container.addView(createActionSheetRow("편집하기") {
            dialog.dismiss()
            showTrimDialog(video)
        })
        container.addView(createActionSheetRow("파일명 변경") {
            dialog.dismiss()
            showRenameDialog(video)
        })
        container.addView(createActionSheetRow("삭제", danger = true) {
            dialog.dismiss()
            confirmAndDelete(video)
        })

        dialog.setContentView(container)
        dialog.show()
    }

    private fun createActionSheetRow(
        label: String,
        danger: Boolean = false,
        onClick: () -> Unit
    ): TextView {
        val color = ContextCompat.getColor(this, if (danger) R.color.danger else R.color.text_primary)
        return TextView(this).apply {
            text = label
            textSize = 16f
            setTextColor(color)
            minimumHeight = dp(50)
            gravity = Gravity.CENTER_VERTICAL
            setPadding(dp(10), 0, dp(10), 0)
            background = ContextCompat.getDrawable(this@MainActivity, R.drawable.bg_dialog_list_selector)
            isClickable = true
            isFocusable = true
            setOnClickListener { onClick() }
        }
    }

    private fun confirmAndDelete(item: VideoItem) {
        MaterialAlertDialogBuilder(this)
            .setTitle("파일 삭제")
            .setMessage("「${item.name}」을 삭제하시겠습니까?\n이 작업은 되돌릴 수 없습니다.")
            .setPositiveButton("삭제") { _, _ -> performDelete(item) }
            .setNegativeButton("취소", null)
            .show()
    }

    /** 앱 전용 폴더의 파일이므로 시스템 삭제 확인창이나 별도 쓰기 권한 없이 바로 삭제 가능. */
    private fun performDelete(item: VideoItem) {
        val file = File(item.path)
        if (file.delete()) {
            allVideoList.remove(item)
            VideoThumbnailCache.deleteFor(applicationContext, item)
            VideoPreferenceManager.deleteRating(item.ratingPreferenceKey())
            VideoPreferenceManager.deleteRating(item.path)
            RatingBackupManager.scheduleExport()
            applyCurrentListState()
            updateEmptyState()
            Toast.makeText(this, "파일이 삭제되었습니다.", Toast.LENGTH_SHORT).show()
        } else {
            Toast.makeText(this, "파일 삭제에 실패했습니다.", Toast.LENGTH_SHORT).show()
        }
    }

    // --- 영상 재생 -------------------------------------------------------------

    private fun openVideoPlayer(video: VideoItem) {
        val savedPkg = VideoPreferenceManager.getDefaultPlayerPackage()
        if (savedPkg != null) {
            launchWithPackage(video, savedPkg)
        } else {
            showPlayerSelectionDialog(video)
        }
    }

    private fun launchWithPackage(video: VideoItem, packageName: String) {
        try {
            val uri = buildVideoUri(video) ?: return
            val intent = Intent(Intent.ACTION_VIEW).apply {
                setDataAndType(uri, "video/*")
                setPackage(packageName)
                addFlags(Intent.FLAG_GRANT_READ_URI_PERMISSION)
            }
            if (intent.resolveActivity(packageManager) != null) {
                startActivity(intent)
                VideoPreferenceManager.saveLastPlayed(video.path)
                adapter.setLastPlayedPath(video.path)
            } else {
                VideoPreferenceManager.clearDefaultPlayer()
                RatingBackupManager.scheduleExport()
                Toast.makeText(this, "기본 플레이어를 찾을 수 없습니다. 다시 선택해 주세요.", Toast.LENGTH_SHORT).show()
                showPlayerSelectionDialog(video)
            }
        } catch (e: Exception) {
            Toast.makeText(this, "영상을 열 수 없습니다: ${e.message}", Toast.LENGTH_SHORT).show()
        }
    }

    // --- 플레이어 선택 다이얼로그 ----------------------------------------------

    private fun showPlayerSelectionDialog(video: VideoItem? = null) {
        val players = getInstalledVideoPlayers()

        if (players.isEmpty()) {
            Toast.makeText(this, "동영상 재생 앱이 설치되어 있지 않습니다.", Toast.LENGTH_SHORT).show()
            return
        }

        val appNames = players.map { it.loadLabel(packageManager).toString() }.toTypedArray()

        MaterialAlertDialogBuilder(this)
            .setTitle("기본 플레이어 선택")
            .setItems(appNames) { _, index ->
                val selected    = players[index]
                val pkgName     = selected.activityInfo.packageName
                val displayName = selected.loadLabel(packageManager).toString()

                VideoPreferenceManager.saveDefaultPlayer(pkgName, displayName)
                RatingBackupManager.scheduleExport()
                Toast.makeText(this, "「$displayName」을(를) 기본 플레이어로 설정했습니다.", Toast.LENGTH_SHORT).show()

                video?.let { launchWithPackage(it, pkgName) }
            }
            .setNegativeButton("취소", null)
            .show()
    }

    private fun showPlayerSettingMenu() {
        val options = MainScreenUiModel.settingsOptions

        MaterialAlertDialogBuilder(this)
            .setTitle("영상 작업")
            .setItems(options) { _, index ->
                when (index) {
                    0 -> pickVideoLauncher.launch(arrayOf("video/*"))
                    1 -> setVideoSelectionAction(VideoSelectionAction.TRIM)
                    2 -> setVideoSelectionAction(VideoSelectionAction.RENAME)
                    3 -> showPlayerSelectionDialog(video = null)
                    4 -> resetDefaultPlayer()
                }
            }
            .setNegativeButton("닫기", null)
            .show()
    }

    // --- 영상 빠른 자르기 ------------------------------------------------------

    private fun setVideoSelectionAction(action: VideoSelectionAction?) {
        if (action != null && allVideoList.isEmpty()) {
            Toast.makeText(this, "선택할 영상이 없습니다.", Toast.LENGTH_SHORT).show()
            return
        }
        selectionAction = action
        if (::adapter.isInitialized) {
            adapter.setSelectionModeLabel(action?.message)
        }
        editSelectionStrip.visibility = if (action != null) View.VISIBLE else View.GONE
        if (action != null) {
            tvEditSelectionMessage.text = action.message
            mainPager.currentItem = MainScreenUiModel.defaultPageIndex
            Toast.makeText(this, action.toast, Toast.LENGTH_SHORT).show()
        }
    }

    private fun showTrimDialog(video: VideoItem) {
        val content = LinearLayout(this).apply {
            orientation = LinearLayout.VERTICAL
            setPadding(dp(18), dp(6), dp(18), dp(4))
            isFocusableInTouchMode = true
        }
        val title = TextView(this).apply {
            text = video.name
            textSize = 14f
            setTextColor(ContextCompat.getColor(this@MainActivity, R.color.text_secondary))
        }
        val duration = TextView(this).apply {
            text = "길이 ${VideoTrimTime.formatTimestamp(video.duration / 1000L)}"
            textSize = 13f
            setTextColor(ContextCompat.getColor(this@MainActivity, R.color.text_muted))
            layoutParams = LinearLayout.LayoutParams(
                LinearLayout.LayoutParams.MATCH_PARENT,
                LinearLayout.LayoutParams.WRAP_CONTENT
            ).apply {
                topMargin = dp(4)
                bottomMargin = dp(12)
            }
        }
        val nameInput = trimEditText(
            label = "파일명",
            value = VideoTrimFileName.defaultEditableName(video.name),
            inputType = InputType.TYPE_CLASS_TEXT,
            parent = content
        )
        val startInput = trimEditText(
            label = "시작 시간",
            value = "00:00:00",
            inputType = InputType.TYPE_CLASS_NUMBER,
            parent = content
        )
        val endInput = trimEditText(
            label = "종료 시간",
            value = VideoTrimTime.formatTimestamp(video.duration / 1000L),
            inputType = InputType.TYPE_CLASS_NUMBER,
            parent = content
        )
        addTrimTimeNormalization(startInput)
        addTrimTimeNormalization(endInput)
        val note = TextView(this).apply {
            text = "빠른 자르기는 화질을 유지하지만 시작 지점이 키프레임 기준으로 조금 달라질 수 있습니다."
            textSize = 12f
            setTextColor(ContextCompat.getColor(this@MainActivity, R.color.text_muted))
            layoutParams = LinearLayout.LayoutParams(
                LinearLayout.LayoutParams.MATCH_PARENT,
                LinearLayout.LayoutParams.WRAP_CONTENT
            ).apply {
                topMargin = dp(10)
            }
        }

        content.addView(title)
        content.addView(duration)
        content.addView(note)

        val dialog = MaterialAlertDialogBuilder(this)
            .setTitle("빠른 자르기")
            .setView(content)
            .setPositiveButton("자르기", null)
            .setNegativeButton("취소") { _, _ -> setVideoSelectionAction(null) }
            .create()

        dialog.setOnShowListener {
            dialog.getButton(AlertDialog.BUTTON_POSITIVE).setOnClickListener {
                val outputName = VideoTrimFileName.outputName(video.name, nameInput.text.toString())
                val startSeconds = VideoTrimTime.parseSeconds(startInput.text.toString())
                val endSeconds = VideoTrimTime.parseSeconds(endInput.text.toString())
                startSeconds?.let { startInput.setText(VideoTrimTime.formatTimestamp(it)) }
                endSeconds?.let { endInput.setText(VideoTrimTime.formatTimestamp(it)) }
                when {
                    startSeconds == null -> Toast.makeText(this, "시작 시간을 확인해 주세요.", Toast.LENGTH_SHORT).show()
                    endSeconds == null -> Toast.makeText(this, "종료 시간을 확인해 주세요.", Toast.LENGTH_SHORT).show()
                    else -> when (VideoTrimValidator.validate(startSeconds, endSeconds, video.duration)) {
                        VideoTrimValidationResult.EndBeforeStart ->
                            Toast.makeText(this, "종료 시간은 시작 시간보다 뒤여야 합니다.", Toast.LENGTH_SHORT).show()
                        VideoTrimValidationResult.EndExceedsDuration ->
                            Toast.makeText(this, "종료 시간이 영상 길이를 넘었습니다.", Toast.LENGTH_SHORT).show()
                        VideoTrimValidationResult.Valid -> {
                        dialog.dismiss()
                        trimVideoFast(video, outputName, startSeconds, endSeconds)
                    }
                    }
                }
            }
        }
        dialog.show()
        dialog.window?.setSoftInputMode(WindowManager.LayoutParams.SOFT_INPUT_ADJUST_RESIZE or WindowManager.LayoutParams.SOFT_INPUT_STATE_ALWAYS_HIDDEN)
        nameInput.clearFocus()
    }

    private fun trimEditText(label: String, value: String, inputType: Int, parent: LinearLayout): EditText {
        val input = TextInputEditText(this).apply {
            setTextColor(ContextCompat.getColor(this@MainActivity, R.color.text_primary))
            setHintTextColor(ContextCompat.getColor(this@MainActivity, R.color.text_muted))
            setText(value)
            this.inputType = inputType
            setSingleLine(true)
            textSize = 15f
            setSelectAllOnFocus(true)
            setPadding(dp(12), dp(0), dp(12), dp(0))
            minHeight = dp(48)
        }

        parent.addView(TextInputLayout(this).apply {
            val primary = ContextCompat.getColor(this@MainActivity, R.color.color_primary)
            val divider = ContextCompat.getColor(this@MainActivity, R.color.divider_soft)
            val textSecondary = ContextCompat.getColor(this@MainActivity, R.color.text_secondary)
            val states = arrayOf(
                intArrayOf(android.R.attr.state_focused),
                intArrayOf()
            )

            hint = label
            boxBackgroundMode = TextInputLayout.BOX_BACKGROUND_OUTLINE
            boxBackgroundColor = ContextCompat.getColor(this@MainActivity, R.color.surface)
            setBoxCornerRadii(
                dp(8).toFloat(),
                dp(8).toFloat(),
                dp(8).toFloat(),
                dp(8).toFloat()
            )
            setBoxStrokeColorStateList(
                ColorStateList(states, intArrayOf(primary, divider))
            )
            defaultHintTextColor = ColorStateList(
                states,
                intArrayOf(primary, textSecondary)
            )
            layoutParams = LinearLayout.LayoutParams(
                LinearLayout.LayoutParams.MATCH_PARENT,
                LinearLayout.LayoutParams.WRAP_CONTENT
            ).apply {
                topMargin = dp(10)
            }
            addView(input)
        })

        return input
    }

    private fun addTrimTimeNormalization(input: EditText) {
        input.setOnFocusChangeListener { view, hasFocus ->
            if (hasFocus) return@setOnFocusChangeListener
            val seconds = VideoTrimTime.parseSeconds((view as EditText).text.toString()) ?: return@setOnFocusChangeListener
            view.setText(VideoTrimTime.formatTimestamp(seconds))
        }
    }

    private fun trimVideoFast(video: VideoItem, requestedOutputName: String, startSeconds: Long, endSeconds: Long) {
        val inputFile = File(video.path)
        if (!inputFile.exists()) {
            Toast.makeText(this, "파일을 찾을 수 없습니다.", Toast.LENGTH_SHORT).show()
            setVideoSelectionAction(null)
            return
        }

        VideoTrimService.start(
            this,
            VideoTrimRequest(
                inputPath = inputFile.absolutePath,
                outputName = requestedOutputName,
                startSeconds = startSeconds,
                endSeconds = endSeconds
            )
        )
        setVideoSelectionAction(null)
        Toast.makeText(this, "자르기를 백그라운드에서 시작했습니다. 알림에서 진행률을 확인하세요.", Toast.LENGTH_LONG).show()
    }

    private fun createTrimProgressDialog(fileName: String): ImportProgressUi {
        val content = LinearLayout(this).apply {
            orientation = LinearLayout.VERTICAL
            setPadding(dp(24), dp(10), dp(24), dp(4))
        }
        val title = TextView(this).apply {
            text = "자르기 중"
            textSize = 16f
            setTextColor(ContextCompat.getColor(this@MainActivity, R.color.text_primary))
        }
        val detail = TextView(this).apply {
            text = fileName
            textSize = 13f
            setTextColor(ContextCompat.getColor(this@MainActivity, R.color.text_secondary))
            layoutParams = LinearLayout.LayoutParams(
                LinearLayout.LayoutParams.MATCH_PARENT,
                LinearLayout.LayoutParams.WRAP_CONTENT
            ).apply {
                topMargin = dp(8)
            }
        }
        val progressBar = ProgressBar(this, null, android.R.attr.progressBarStyleHorizontal).apply {
            max = 100
            progress = 0
            layoutParams = LinearLayout.LayoutParams(
                LinearLayout.LayoutParams.MATCH_PARENT,
                LinearLayout.LayoutParams.WRAP_CONTENT
            ).apply {
                topMargin = dp(14)
            }
        }
        val percent = TextView(this).apply {
            text = "0%"
            gravity = Gravity.END
            textSize = 12f
            setTextColor(ContextCompat.getColor(this@MainActivity, R.color.text_muted))
        }
        content.addView(title)
        content.addView(detail)
        content.addView(progressBar)
        content.addView(percent)

        val dialog = MaterialAlertDialogBuilder(this)
            .setView(content)
            .setNegativeButton("취소", null)
            .create()

        dialog.setCancelable(false)
        dialog.show()
        dialog.getButton(AlertDialog.BUTTON_NEGATIVE).setOnClickListener {
            activeFfmpegSessionId?.let(FFmpegKit::cancel)
            it.isEnabled = false
            title.text = "자르기 취소 중"
        }

        return ImportProgressUi(dialog, title, detail, progressBar, percent)
    }

    private fun resetDefaultPlayer() {
        VideoPreferenceManager.clearDefaultPlayer()
        RatingBackupManager.scheduleExport()
        Toast.makeText(this, "기본 플레이어 설정이 초기화되었습니다.", Toast.LENGTH_SHORT).show()
    }

    private fun showRenameDialog(video: VideoItem) {
        val content = LinearLayout(this).apply {
            orientation = LinearLayout.VERTICAL
            setPadding(dp(18), dp(6), dp(18), dp(4))
            isFocusableInTouchMode = true
        }
        content.addView(TextView(this).apply {
            text = video.name
            textSize = 14f
            setTextColor(ContextCompat.getColor(this@MainActivity, R.color.text_secondary))
            layoutParams = LinearLayout.LayoutParams(
                LinearLayout.LayoutParams.MATCH_PARENT,
                LinearLayout.LayoutParams.WRAP_CONTENT
            ).apply {
                bottomMargin = dp(8)
            }
        })
        val nameInput = trimEditText(
            label = "파일명",
            value = VideoRenameFileName.defaultEditableName(video.name),
            inputType = InputType.TYPE_CLASS_TEXT,
            parent = content
        )

        val dialog = MaterialAlertDialogBuilder(this)
            .setTitle("파일명 변경")
            .setView(content)
            .setPositiveButton("변경", null)
            .setNegativeButton("취소") { _, _ -> setVideoSelectionAction(null) }
            .create()

        dialog.setOnShowListener {
            dialog.getButton(AlertDialog.BUTTON_POSITIVE).setOnClickListener {
                val outputName = VideoRenameFileName.outputName(video.name, nameInput.text.toString())
                when {
                    outputName.isBlank() -> Toast.makeText(this, "파일명을 입력해 주세요.", Toast.LENGTH_SHORT).show()
                    outputName == video.name -> Toast.makeText(this, "변경할 파일명이 같습니다.", Toast.LENGTH_SHORT).show()
                    else -> {
                        dialog.dismiss()
                        renameVideoFile(video, outputName)
                    }
                }
            }
        }
        dialog.show()
        dialog.window?.setSoftInputMode(WindowManager.LayoutParams.SOFT_INPUT_ADJUST_RESIZE or WindowManager.LayoutParams.SOFT_INPUT_STATE_ALWAYS_HIDDEN)
        nameInput.clearFocus()
    }

    private fun renameVideoFile(video: VideoItem, requestedOutputName: String) {
        val sourceFile = File(video.path)
        if (!sourceFile.exists()) {
            Toast.makeText(this, "파일을 찾을 수 없습니다.", Toast.LENGTH_SHORT).show()
            setVideoSelectionAction(null)
            return
        }

        val targetFile = uniqueVideoFile(requestedOutputName)
        if (!sourceFile.renameTo(targetFile)) {
            Toast.makeText(this, "파일명 변경에 실패했습니다.", Toast.LENGTH_SHORT).show()
            return
        }

        VideoThumbnailCache.deleteFor(applicationContext, video)
        if (video.rating != 0f) {
            VideoPreferenceManager.saveRating(targetFile.name, video.rating)
        }
        VideoPreferenceManager.deleteRating(video.ratingPreferenceKey())
        VideoPreferenceManager.deleteRating(video.path)
        RatingBackupManager.scheduleExport()
        setVideoSelectionAction(null)
        loadVideos()
        Toast.makeText(this, "파일명 변경 완료: ${targetFile.name}", Toast.LENGTH_LONG).show()
    }

    // --- 플레이어 앱 조회 ------------------------------------------------------

    private fun getInstalledVideoPlayers(): List<ResolveInfo> {
        val intent = Intent(Intent.ACTION_VIEW).apply {
            setDataAndType(Uri.parse("file://dummy.mp4"), "video/*")
        }
        return if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.TIRAMISU) {
            packageManager.queryIntentActivities(
                intent,
                PackageManager.ResolveInfoFlags.of(PackageManager.MATCH_DEFAULT_ONLY.toLong())
            )
        } else {
            @Suppress("DEPRECATION")
            packageManager.queryIntentActivities(intent, PackageManager.MATCH_DEFAULT_ONLY)
        }
    }

    // --- URI 생성 헬퍼 --------------------------------------------------------

    private fun buildVideoUri(video: VideoItem): Uri? {
        val file = File(video.path)
        if (!file.exists()) {
            Toast.makeText(this, "파일을 찾을 수 없습니다.", Toast.LENGTH_SHORT).show()
            return null
        }
        return if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.N) {
            FileProvider.getUriForFile(this, "${packageName}.fileprovider", file)
        } else {
            Uri.fromFile(file)
        }
    }

    // --- UI 상태 헬퍼 ---------------------------------------------------------

    private fun showLoading(show: Boolean) {
        progressBar.visibility  = if (show) View.VISIBLE else View.GONE
        recyclerView.visibility = if (show) View.GONE    else View.VISIBLE
    }

    private fun updateEmptyState() {
        val isEmpty = videoList.isEmpty()
        if (isEmpty) {
            tvEmpty.text = "영상 파일이 없습니다.\n영상 탭의 가져오기로 동영상을 추가할 수 있습니다."
        }
        tvEmpty.visibility      = if (isEmpty) View.VISIBLE else View.GONE
        recyclerView.visibility = if (isEmpty) View.GONE    else View.VISIBLE
    }

    private fun createDialogChoiceRow(
        label: String,
        checked: Boolean,
        onClick: () -> Unit
    ): LinearLayout {
        val accent = ContextCompat.getColor(this, R.color.color_accent)
        val muted = ContextCompat.getColor(this, R.color.text_muted)
        val textPrimary = ContextCompat.getColor(this, R.color.text_primary)
        val tint = ColorStateList(
            arrayOf(intArrayOf(android.R.attr.state_checked), intArrayOf()),
            intArrayOf(accent, muted)
        )

        return LinearLayout(this).apply {
            orientation = LinearLayout.HORIZONTAL
            gravity = android.view.Gravity.CENTER_VERTICAL
            minimumHeight = dp(48)
            setPadding(dp(6), dp(4), dp(10), dp(4))
            background = ContextCompat.getDrawable(this@MainActivity, R.drawable.bg_dialog_list_selector)
            isClickable = true
            isFocusable = true
            setOnClickListener { onClick() }

            addView(RadioButton(this@MainActivity).apply {
                isChecked = checked
                isClickable = false
                buttonTintList = tint
                layoutParams = LinearLayout.LayoutParams(
                    LinearLayout.LayoutParams.WRAP_CONTENT,
                    LinearLayout.LayoutParams.WRAP_CONTENT
                )
            })

            addView(TextView(this@MainActivity).apply {
                text = label
                textSize = 15f
                setTextColor(textPrimary)
                layoutParams = LinearLayout.LayoutParams(
                    0,
                    LinearLayout.LayoutParams.WRAP_CONTENT,
                    1f
                ).apply {
                    leftMargin = dp(6)
                }
            })
        }
    }

    private fun dp(value: Int): Int =
        (value * resources.displayMetrics.density).toInt()

    private fun showRatingFilterDialog() {
        val labels = arrayOf("전체", "5점", "4점", "3점", "2점", "1점", "미평가")
        val filters = listOf(
            RatingFilter.ALL,
            RatingFilter.Stars(5),
            RatingFilter.Stars(4),
            RatingFilter.Stars(3),
            RatingFilter.Stars(2),
            RatingFilter.Stars(1),
            RatingFilter.UNRATED
        )
        val checkedIndex = filters.indexOfFirst { it == currentFilter }.coerceAtLeast(0)

        val content = LinearLayout(this).apply {
            orientation = LinearLayout.VERTICAL
            setPadding(dp(20), dp(8), dp(20), dp(4))
        }
        lateinit var dialog: AlertDialog
        labels.forEachIndexed { index, label ->
            content.addView(
                createDialogChoiceRow(
                    label = label,
                    checked = index == checkedIndex
                ) {
                    currentFilter = filters[index]
                    VideoPreferenceManager.saveRatingFilter(currentFilter)
                    currentSortMode = VideoSortMode.RATING_DESC
                    applyCurrentListState()
                    dialog.dismiss()
                }
            )
        }

        dialog = MaterialAlertDialogBuilder(this)
            .setTitle("별점 선택")
            .setView(content)
            .setNegativeButton("닫기", null)
            .create()
        dialog.show()
    }

    private fun showDateSortDialog() {
        val modes = listOf(VideoSortMode.NEWEST_FIRST, VideoSortMode.OLDEST_FIRST)
        val labels = modes.map { it.label }.toTypedArray()
        val checkedIndex = modes.indexOf(currentSortMode).coerceAtLeast(0)

        val content = LinearLayout(this).apply {
            orientation = LinearLayout.VERTICAL
            setPadding(dp(20), dp(8), dp(20), dp(4))
        }
        lateinit var dialog: AlertDialog
        labels.forEachIndexed { index, label ->
            content.addView(
                createDialogChoiceRow(
                    label = label,
                    checked = index == checkedIndex
                ) {
                    currentSortMode = modes[index]
                    applyCurrentListState()
                    dialog.dismiss()
                }
            )
        }

        dialog = MaterialAlertDialogBuilder(this)
            .setTitle("날짜 정렬")
            .setView(content)
            .setNegativeButton("닫기", null)
            .create()
        dialog.show()
    }

    private fun applyCurrentListState() {
        val filtered = filterVideos(allVideoList, currentFilter)
        val sorted = when (currentSortMode) {
            VideoSortMode.RATING_DESC -> filtered.sortedWith(
                compareByDescending<VideoItem> { it.rating }.thenByDescending { it.dateModified }
            )
            VideoSortMode.NEWEST_FIRST -> filtered.sortedByDescending { it.dateModified }
            VideoSortMode.OLDEST_FIRST -> filtered.sortedBy { it.dateModified }
            VideoSortMode.RANDOM -> filtered
        }
        adapter.updateList(sorted)
        updateSortButtons()
        updateEmptyState()
    }

    private fun updateSortButtons() {
        btnSortRating.text = if (currentSortMode == VideoSortMode.RATING_DESC) {
            "별점순: ${currentFilter.label()}"
        } else {
            "별점: ${currentFilter.label()}"
        }
        btnSortDate.text = when (currentSortMode) {
            VideoSortMode.NEWEST_FIRST -> VideoSortMode.NEWEST_FIRST.label
            VideoSortMode.OLDEST_FIRST -> VideoSortMode.OLDEST_FIRST.label
            VideoSortMode.RATING_DESC,
            VideoSortMode.RANDOM -> VideoSortMode.NEWEST_FIRST.label
        }
        btnShuffle.text = ""
        btnShuffle.contentDescription = if (currentSortMode == VideoSortMode.RANDOM) {
            "필터 결과 랜덤 새로고침 적용됨"
        } else {
            "필터 결과 랜덤 새로고침"
        }
    }

    private fun RatingFilter.label(): String = when (this) {
        RatingFilter.ALL -> "전체"
        is RatingFilter.Stars -> "${stars}점"
        RatingFilter.UNRATED -> "미평가"
    }

    private class MainPagerAdapter(
        private val pages: List<View>
    ) : RecyclerView.Adapter<MainPagerAdapter.PageViewHolder>() {

        override fun onCreateViewHolder(parent: ViewGroup, viewType: Int): PageViewHolder =
            PageViewHolder(pages[viewType])

        override fun onBindViewHolder(holder: PageViewHolder, position: Int) = Unit

        override fun getItemCount(): Int = pages.size

        override fun getItemViewType(position: Int): Int = position

        class PageViewHolder(view: View) : RecyclerView.ViewHolder(view)
    }

    private enum class VideoSelectionAction(
        val message: String,
        val toast: String
    ) {
        TRIM(
            message = "편집할 영상을 선택하세요",
            toast = "편집할 영상을 목록에서 선택하세요."
        ),
        RENAME(
            message = "이름을 바꿀 영상을 선택하세요",
            toast = "이름을 바꿀 영상을 목록에서 선택하세요."
        )
    }

    companion object {
        private const val BIOMETRIC_AUTHENTICATORS = BiometricManager.Authenticators.BIOMETRIC_STRONG
        private const val REQUEST_POST_NOTIFICATIONS = 2101
    }
}

private data class ImportVideoMetadata(
    val title: String,
    val sizeBytes: Long? = null,
    val width: Int? = null,
    val height: Int? = null,
    val bitrate: Int? = null,
    val durationMs: Long? = null,
    val codecMime: String? = null,
    val thumbnail: Bitmap? = null
)

private data class ImportVideoSelection(
    val uri: Uri,
    val metadata: ImportVideoMetadata
)

private data class ImportVideosResult(
    val files: List<File>,
    val sourceDeletion: VideoSourceDeletionSummary
)
