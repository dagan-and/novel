package com.kys.videomanager.video
import com.kys.videomanager.R

import android.content.Context
import android.graphics.Bitmap
import android.media.MediaMetadataRetriever
import android.view.LayoutInflater
import android.view.View
import android.view.ViewGroup
import android.widget.ImageView
import android.widget.RatingBar
import android.widget.TextView
import androidx.cardview.widget.CardView
import androidx.core.content.ContextCompat
import androidx.recyclerview.widget.RecyclerView
import com.bumptech.glide.Glide
import com.bumptech.glide.load.resource.bitmap.CenterCrop
import com.bumptech.glide.load.resource.bitmap.RoundedCorners
import com.bumptech.glide.request.RequestOptions
import com.google.android.material.dialog.MaterialAlertDialogBuilder
import kotlinx.coroutines.*
import java.text.SimpleDateFormat
import java.util.*

/**
 * 영상 목록 RecyclerView 어댑터
 *
 * 썸네일 로딩: 앱 캐시 폴더의 jpg 썸네일을 먼저 사용하고, 없을 때만
 * MediaMetadataRetriever.getFrameAtTime() 으로 추출해 저장한다.
 *
 * 뷰 재사용 처리:
 *   각 ViewHolder가 Job 을 소유 → onViewRecycled() 에서 취소
 *   → 스크롤 중 이전 요청이 뒤늦게 덮어쓰는 문제 방지
 *
 * 인터랙션 (서로 겹치지 않는 별도 동작):
 *   짧은 클릭     → 외부 플레이어 실행
 *   별점 영역 탭  → 별점 입력 팝업 표시 → 저장
 *   긴 클릭       → 편집하기/파일명 변경/삭제 액션 시트
 */
class VideoAdapter(
    private val context: Context,
    private val videoList: MutableList<VideoItem>,
    private val onItemClick: (VideoItem) -> Unit,
    private val onRatingChanged: (VideoItem, Float) -> Unit,
    private val onItemLongPress: (VideoItem) -> Unit
) : RecyclerView.Adapter<VideoAdapter.VideoViewHolder>() {
    private var selectionModeLabel: String? = null
    private var lastPlayedPath: String? = null

    // --- ViewHolder ------------------------------------------------------------

    inner class VideoViewHolder(itemView: View) : RecyclerView.ViewHolder(itemView) {
        val ivThumbnail: ImageView  = itemView.findViewById(R.id.iv_thumbnail)
        val tvName: TextView        = itemView.findViewById(R.id.tv_name)
        val tvDuration: TextView    = itemView.findViewById(R.id.tv_duration)
        val tvSize: TextView        = itemView.findViewById(R.id.tv_size)
        val tvDate: TextView        = itemView.findViewById(R.id.tv_date)
        val ratingContainer: View    = itemView.findViewById(R.id.rating_container)
        val ratingBar: RatingBar    = itemView.findViewById(R.id.rating_bar)
        val tvRatingValue: TextView = itemView.findViewById(R.id.tv_rating_value)
        val recentlyPlayedStripe: View = itemView.findViewById(R.id.recently_played_stripe)
        val tvRecentlyPlayedBadge: TextView = itemView.findViewById(R.id.tv_recently_played_badge)

        // 이 ViewHolder 에서 실행 중인 썸네일 로딩 Job
        var thumbnailJob: Job? = null
    }

    // --- Adapter 오버라이드 ----------------------------------------------------

    override fun onCreateViewHolder(parent: ViewGroup, viewType: Int): VideoViewHolder {
        val view = LayoutInflater.from(context)
            .inflate(R.layout.item_video, parent, false)
        return VideoViewHolder(view)
    }

    override fun getItemCount(): Int = videoList.size

    override fun onBindViewHolder(holder: VideoViewHolder, position: Int) {
        val item = videoList[position]
        bindSelectionMode(holder)
        bindThumbnail(holder, item)
        bindTextInfo(holder, item)
        bindRatingBar(holder, item)
        bindRecentlyPlayed(holder, item)
        bindClickListeners(holder, item)
    }

    /**
     * ViewHolder 가 RecyclerView 풀로 반환될 때 호출
     * → 진행 중인 썸네일 로딩 코루틴 취소 + Glide 요청 해제
     */
    override fun onViewRecycled(holder: VideoViewHolder) {
        super.onViewRecycled(holder)
        holder.thumbnailJob?.cancel()
        holder.thumbnailJob = null
        Glide.with(context.applicationContext).clear(holder.ivThumbnail)
    }

    // --- 썸네일 로딩 ----------------------------------------------------------

    /**
     * 썸네일을 캐시에서 찾고, 없을 때만 코루틴으로 비동기 추출 후 Glide 로 표시
     *
     * 로딩 순서:
     *  1. 즉시 플레이스홀더 표시
     *  2. 캐시 파일이 있으면 바로 Glide 로 표시
     *  3. 없으면 IO 스레드에서 extractThumbnail() 실행 후 jpg 캐시 저장
     *  4. 캐시 파일 또는 비트맵이 성공적으로 나오면 Main 스레드에서 Glide 로 표시
     *  5. ViewHolder 가 재사용되면(onViewRecycled) Job 취소 → 결과 무시
     */
    private fun bindThumbnail(holder: VideoViewHolder, item: VideoItem) {
        // 이전 Job 취소 (빠른 스크롤 시 중복 요청 방지)
        holder.thumbnailJob?.cancel()

        // 즉시 플레이스홀더 표시
        holder.ivThumbnail.setImageResource(R.drawable.ic_video_placeholder)

        val requestOptions = RequestOptions()
            .transform(CenterCrop(), RoundedCorners(8))

        val cachedFile = VideoThumbnailCache.existingFileFor(context.applicationContext, item)
        if (cachedFile != null) {
            Glide.with(context.applicationContext)
                .load(cachedFile)
                .apply(requestOptions)
                .placeholder(R.drawable.ic_video_placeholder)
                .error(R.drawable.ic_video_placeholder)
                .into(holder.ivThumbnail)
            return
        }

        // 새 코루틴으로 썸네일 로딩
        holder.thumbnailJob = CoroutineScope(Dispatchers.Main + SupervisorJob()).launch {
            val thumbnail = withContext(Dispatchers.IO) {
                val bitmap = extractThumbnail(item) ?: return@withContext null
                VideoThumbnailCache.save(
                    bitmap = bitmap,
                    outputFile = VideoThumbnailCache.fileFor(context.applicationContext, item)
                ) ?: bitmap
            }
            // Job 이 취소되지 않았을 때만 UI 업데이트
            if (isActive && thumbnail != null) {
                Glide.with(context.applicationContext)
                    .load(thumbnail)
                    .apply(requestOptions)
                    .placeholder(R.drawable.ic_video_placeholder)
                    .error(R.drawable.ic_video_placeholder)
                    .into(holder.ivThumbnail)
            }
        }
    }

    /**
     * MediaMetadataRetriever 로 특정 시점 프레임 추출
     *
     * 검은 첫 프레임 회피 전략:
     *   - 영상 길이 < 2초  → 정중앙(50%) 프레임
     *   - 영상 길이 ≥ 2초  → 1초 또는 10% 중 작은 값
     *
     * 예) 10분짜리 영상 → 1초 지점
     *     0.5초짜리 영상 → 0.25초 지점
     */
    private fun extractThumbnail(item: VideoItem): Bitmap? {
        val retriever = MediaMetadataRetriever()
        return try {
            retriever.setDataSource(item.path)

            // 영상 길이 확보 (VideoItem.duration 이 0이면 메타데이터에서 재조회)
            val durationMs: Long = if (item.duration > 0) {
                item.duration
            } else {
                retriever.extractMetadata(MediaMetadataRetriever.METADATA_KEY_DURATION)
                    ?.toLongOrNull() ?: 0L
            }

            val seekTimeUs: Long = when {
                durationMs <= 0    -> 0L
                durationMs < 2_000 -> durationMs * 1_000L / 2          // 50% (짧은 영상)
                else               -> minOf(1_000_000L, durationMs * 1_000L / 10)  // 1s or 10%
            }

            retriever.getFrameAtTime(seekTimeUs, MediaMetadataRetriever.OPTION_CLOSEST_SYNC)
        } catch (_: Exception) {
            null
        } finally {
            try { retriever.release() } catch (_: Exception) { }
        }
    }

    // --- 나머지 바인딩 헬퍼 ---------------------------------------------------

    private fun bindTextInfo(holder: VideoViewHolder, item: VideoItem) {
        holder.tvName.text     = item.name
        holder.tvDuration.text = formatDuration(item.duration)
        holder.tvSize.text     = formatSize(item.size)
        holder.tvDate.text     = formatDate(item.dateModified)
    }

    private fun bindSelectionMode(holder: VideoViewHolder) {
        val active = selectionModeLabel != null
        val card = holder.itemView as? CardView ?: return
        val backgroundColor = ContextCompat.getColor(
            context,
            if (active) R.color.surface_tint else R.color.surface
        )
        card.setCardBackgroundColor(backgroundColor)
        card.cardElevation = (if (active) 5f else 2f) * context.resources.displayMetrics.density
        holder.itemView.contentDescription = selectionModeLabel?.let { "$it: ${holder.tvName.text}" }
    }

    /** 인라인 별점바는 현재 별점을 보여주는 표시 전용(indicator)이며 터치로 조작되지 않는다. */
    private fun bindRatingBar(holder: VideoViewHolder, item: VideoItem) {
        holder.ratingBar.rating = item.rating
        holder.tvRatingValue.text = formatRating(item.rating)
    }

    private fun bindRecentlyPlayed(holder: VideoViewHolder, item: VideoItem) {
        val highlighted = RecentlyPlayedHighlightPolicy.isHighlighted(item.path, lastPlayedPath)
        holder.recentlyPlayedStripe.visibility = if (highlighted) View.VISIBLE else View.GONE
        holder.tvRecentlyPlayedBadge.visibility = if (highlighted) View.VISIBLE else View.GONE
    }

    private fun bindClickListeners(holder: VideoViewHolder, item: VideoItem) {
        holder.itemView.setOnClickListener { onItemClick(item) }
        holder.itemView.setOnLongClickListener {
            onItemLongPress(item)
            true
        }
        holder.ratingContainer.setOnClickListener {
            val position = holder.bindingAdapterPosition
            if (position != RecyclerView.NO_POSITION) {
                showRatingDialog(item, position)
            }
        }
    }

    // --- 별점 입력 팝업 --------------------------------------------------------

    private fun showRatingDialog(item: VideoItem, position: Int) {
        val dialogView = LayoutInflater.from(context)
            .inflate(R.layout.dialog_rating, null)

        val tvTitle     = dialogView.findViewById<TextView>(R.id.tv_dialog_title)
        val ratingBar   = dialogView.findViewById<RatingBar>(R.id.rating_bar_dialog)
        val tvRatingVal = dialogView.findViewById<TextView>(R.id.tv_dialog_rating_value)

        tvTitle.text     = item.name
        ratingBar.rating = item.rating
        tvRatingVal.text = formatRatingFull(item.rating)

        ratingBar.setOnRatingBarChangeListener { _, rating, _ ->
            tvRatingVal.text = formatRatingFull(rating)
        }

        MaterialAlertDialogBuilder(context)
            .setTitle("별점 부여")
            .setView(dialogView)
            .setPositiveButton("저장") { _, _ ->
                val newRating = ratingBar.rating
                item.rating   = newRating
                onRatingChanged(item, newRating)
                notifyItemChanged(position)
            }
            .setNegativeButton("취소", null)
            .show()
    }

    // --- 공개 메서드 -----------------------------------------------------------

    fun updateList(newList: List<VideoItem>) {
        videoList.clear()
        videoList.addAll(newList)
        notifyDataSetChanged()
    }

    fun setSelectionModeLabel(label: String?) {
        selectionModeLabel = label
        notifyDataSetChanged()
    }

    fun setLastPlayedPath(path: String?) {
        lastPlayedPath = path
        notifyDataSetChanged()
    }

    fun shuffle() {
        videoList.shuffle()
        notifyDataSetChanged()
    }

    fun sortByRatingDesc() {
        videoList.sortWith(compareByDescending<VideoItem> { it.rating }.thenBy { it.name })
        notifyDataSetChanged()
    }

    // --- 포맷 유틸 ------------------------------------------------------------

    private fun formatDuration(ms: Long): String {
        val totalSec = ms / 1000
        val h = totalSec / 3600
        val m = (totalSec % 3600) / 60
        val s = totalSec % 60
        return if (h > 0) "%d:%02d:%02d".format(h, m, s)
        else              "%02d:%02d".format(m, s)
    }

    private fun formatSize(bytes: Long): String =
        VideoListFormatter.formatSize(bytes)

    private fun formatDate(epochSec: Long): String =
        SimpleDateFormat("yyyy-MM-dd", Locale.getDefault())
            .format(Date(epochSec * 1000L))

    private fun formatRating(rating: Float): String =
        "★ %.1f".format(rating)

    private fun formatRatingFull(rating: Float): String =
        "★ %.1f / 5.0".format(rating)
}
