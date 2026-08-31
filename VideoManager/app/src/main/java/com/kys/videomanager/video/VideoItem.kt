package com.kys.videomanager.video

/**
 * 영상 파일 하나를 표현하는 데이터 클래스
 *
 * @param name          파일 이름
 * @param path          절대 경로 – 파일 열기와 삭제에 사용됨
 * @param duration      재생 시간 (밀리초)
 * @param size          파일 크기 (바이트)
 * @param dateModified  마지막 수정 시각 (Unix 초)
 * @param rating        사용자 별점 (0.0 ~ 5.0, 0.5 단위)
 */
data class VideoItem(
    val name: String,
    val path: String,
    val duration: Long,
    val size: Long,
    val dateModified: Long,
    var rating: Float = 0f
)
