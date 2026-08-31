# 평점 필터 칩 + 롱클릭 메뉴 + 파일 삭제 설계

## 개요

VideoManager 앱에 세 가지 기능을 추가한다:
1. 상단 평점 필터 칩 (가로 스크롤)
2. 롱클릭 액션 메뉴 (평점 주기 / 파일 삭제)
3. 파일 직접 삭제 (API별 처리)

---

## 1. 평점 필터 칩

### UI
- `activity_main.xml`의 버튼 행 아래, RecyclerView 위에 `HorizontalScrollView + ChipGroup` 배치
- 칩 목록: `전체` `★5` `★4` `★3` `★2` `★1` `미평가` (7개)
- 단일 선택 (`app:singleSelection="true"`), 기본 선택: `전체`

### 동작
- `MainActivity`에 `allVideoList: List<VideoItem>` 원본 보관
- 칩 선택 시 `allVideoList`를 필터링 → `adapter.updateList(filtered)`
- 필터 기준:
  - `★N` 칩: `rating >= N && rating < N+1` (단, `★5`는 `rating == 5.0`)
  - `미평가`: `rating == 0f`
  - `전체`: 필터 없음
- 셔플/별점순 정렬은 현재 필터 결과 위에서 동작
- 영상 로딩 완료 시 필터 초기화 (`전체` 칩 선택)

---

## 2. 롱클릭 액션 메뉴

### 기존 동작 변경
- 기존: 롱클릭 → 바로 평점 다이얼로그
- 변경: 롱클릭 → `MaterialAlertDialogBuilder` 아이템 메뉴

### 메뉴 구성
```
[ 파일명 ]
──────────────
  ★ 평점 주기
  🗑 파일 삭제
```

- **평점 주기**: 기존 `showRatingDialog()` 그대로 호출
- **파일 삭제**: `onDeleteItem(VideoItem)` 콜백 호출

### VideoAdapter 변경
- 생성자에 `onDeleteItem: (VideoItem) -> Unit` 콜백 추가
- `bindClickListeners()`에서 롱클릭 → `showActionMenu()` 호출
- `showRatingDialog()`는 그대로 유지

---

## 3. 파일 삭제

### 삭제 흐름
1. 확인 다이얼로그 표시: "파일명을 삭제하시겠습니까? 이 작업은 되돌릴 수 없습니다."
2. 확인 시 API별 분기 처리
3. 성공 시 `videoList`와 `allVideoList`에서 제거 → `adapter.updateList()` 갱신

### API별 처리
| API 레벨 | 방식 |
|---------|------|
| 30+ (Android 11+) | `MediaStore.createDeleteRequest()` → 시스템 권한 팝업 → 결과 수신 |
| 29 이하 | `File.delete()` + `ContentResolver.delete()` |

### 권한
- `AndroidManifest.xml`에 `WRITE_EXTERNAL_STORAGE` 추가 (`maxSdkVersion="28"`)
- API 29 이하에서 권한 없으면 요청 후 삭제 재시도

---

## 수정 파일

| 파일 | 변경 내용 |
|------|---------|
| `activity_main.xml` | ChipGroup 추가 |
| `VideoAdapter.kt` | `onDeleteItem` 콜백, `showActionMenu()` 추가, 롱클릭 동작 변경 |
| `MainActivity.kt` | `allVideoList` 관리, 필터 로직, 삭제 처리, 권한 처리, ActivityResultLauncher 추가 |
| `AndroidManifest.xml` | `WRITE_EXTERNAL_STORAGE` 권한 추가 |
