# 별점/설정 자동 백업 (공용 저장소 JSON 동기화) 설계

## 배경

현재 영상 별점과 기본 플레이어 설정은 `SharedPreferences`(`VideoPreferenceManager`)에만 저장된다. 이 데이터는 앱 전용 내부 저장소에 있어 **앱을 삭제하면 즉시 사라진다**. 영상 파일 자체는 MediaStore를 통해 참조만 하므로 삭제해도 안전하지만, 별점/설정은 그렇지 않다.

이 기능은 별점/설정 변경을 공용 저장소(Downloads)의 JSON 파일에 자동으로 동기화하여, 앱을 삭제 후 재설치해도 이전 데이터를 복원할 수 있게 한다.

## 목표

- 수동 UI(내보내기/가져오기 버튼) 없이, 데이터 변경 시 자동으로 백업
- 앱 재설치 후 로컬 데이터가 비어있을 때 자동으로 백업에서 복원
- 기존 기능(영상 목록 로딩, 별점 매기기, 삭제, 기본 플레이어 선택)에 영향 없음
- 백업 실패가 앱 크래시나 핵심 기능 장애로 이어지지 않음 (best-effort)

## 비목표

- 여러 백업 버전 관리(타임스탬프 파일 등) — 항상 단일 파일을 덮어씀
- 사용자가 백업 위치를 직접 선택(SAF 피커) — 고정 경로 사용
- 클라우드 동기화 — 로컬 기기의 공용 저장소만 대상

## 데이터 포맷

`Downloads/VideoManager/video_ratings_backup.json`

```json
{
  "version": 1,
  "ratings": {
    "/storage/emulated/0/DCIM/video1.mp4": 4.5,
    "/storage/emulated/0/DCIM/video2.mp4": 3.0
  },
  "defaultPlayer": {
    "packageName": "com.mxtech.videoplayer.ad",
    "appName": "MX Player"
  }
}
```

`defaultPlayer`는 설정되지 않은 경우 `null`.

## 컴포넌트

### `RatingBackupManager` (신규 object, `VideoPreferenceManager`와 동일한 패키지)

`VideoPreferenceManager`를 수정하지 않고 독립된 객체로 분리한다. 백업은 "저장"과 별개의 관심사이며, 이렇게 분리하면 `VideoPreferenceManager`는 계속 순수 로컬 읽기/쓰기만 책임진다.

```kotlin
object RatingBackupManager {
    fun init(context: Context)

    /** 현재 별점 + 기본 플레이어 정보를 코루틴(IO)으로 백업 파일에 덮어쓴다. Fire-and-forget. */
    fun scheduleExport()

    /**
     * 로컬 데이터(별점 + 기본 플레이어)가 완전히 비어있을 때만 백업 파일을 읽어 복원한다.
     * @return 실제로 복원이 일어났으면 true
     */
    suspend fun restoreIfLocalEmpty(): Boolean
}
```

### 저장 위치 / API 호환성 (minSdk 21, targetSdk 34)

- **API 29+**: `MediaStore.Downloads` 컬렉션 사용. `RELATIVE_PATH = Environment.DIRECTORY_DOWNLOADS + "/VideoManager"`, `DISPLAY_NAME = "video_ratings_backup.json"`. 매 export 시 기존 행을 쿼리해 있으면 `openOutputStream(uri, "wt")`로 덮어쓰고, 없으면 새로 insert. 별도 권한 불필요(스코프드 스토리지 예외).
- **API 21~28**: `Environment.getExternalStoragePublicDirectory(DIRECTORY_DOWNLOADS)/VideoManager/video_ratings_backup.json`에 `java.io.File`로 직접 읽기/쓰기. `WRITE_EXTERNAL_STORAGE` 권한 필요.
  - 권한이 없으면 **새로 권한 요청 팝업을 띄우지 않고 조용히 건너뛴다** (백그라운드 부가기능이 예기치 않게 권한 팝업을 띄우는 것을 방지). 이미 다른 흐름(파일 삭제)에서 권한이 부여된 상태라면 정상 동작.

### MainActivity 연동 지점

- `onCreate()`: `VideoPreferenceManager.init(this)` 직후, `checkPermissionAndLoad()`(영상 목록 로딩) 전에 `RatingBackupManager.restoreIfLocalEmpty()`를 호출(suspend). `true`가 반환되면 Toast: "이전 데이터를 백업에서 복원했습니다."
- 다음 호출 직후에 각각 `RatingBackupManager.scheduleExport()` 추가:
  - `onRatingChanged` 콜백 내 `VideoPreferenceManager.saveRating(...)` 호출 후
  - `deleteLauncher` 콜백 내 `VideoPreferenceManager.deleteRating(...)` 호출 후
  - `showPlayerSelectionDialog`의 `saveDefaultPlayer(...)` 호출 후
  - `showPlayerSettingMenu`의 `clearDefaultPlayer()` 호출 후

## 에러 처리

- 모든 파일 I/O는 try/catch로 감싸고 실패 시 `Log.w`로만 기록, 예외를 전파하지 않는다.
- Export 실패는 별점 저장(SharedPreferences, 이미 즉시 완료됨)에 영향을 주지 않는다.
- Import 시 JSON 파싱 오류/파일 손상은 복원을 건너뛰고 앱은 정상 진행한다.

## 테스트 계획

1. 별점 부여 → 파일 관리자에서 `Downloads/VideoManager/video_ratings_backup.json` 생성 확인
2. 앱 데이터 삭제(또는 삭제 후 재설치) → 재실행 시 Toast로 복원 확인 + 별점/기본 플레이어 유지 확인
3. 최초 설치(백업 파일 없음) 상태에서 크래시 없이 정상 동작
4. API 28 이하 환경에서 `WRITE_EXTERNAL_STORAGE` 미승인 상태로도 앱이 정상 동작(백업만 스킵)하는지 확인
5. 로컬에 이미 데이터가 있는 상태로 앱을 재시작했을 때 백업 파일 내용으로 덮어써지지 않는지(merge 안 함) 확인
