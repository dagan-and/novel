# HLS 다운로드 토큰 자동 갱신 + 수동 제어 버튼 설계

## 배경

`hublk-078` 다운로드가 시작부터 `Illegal character in path`로 실패하던 문제는 원인을 찾아 수정했다
(`HlsRequestProbe.buildHeaders`가 WebView의 `Accept-Encoding` 헤더를 그대로 복사해 쓰던 것을,
항상 `identity`로 강제하도록 변경 — 이미 반영/검증 완료, 이 스펙의 범위 아님).

그 과정에서 발견된 별도 문제: 재생목록(m3u8) URL은 CDN이 서명한 토큰(`e=`, `h=`, `s=`, `x=` 등 쿼리
파라미터)을 포함하며, 이 토큰은 WebView로 그 영상 페이지를 열 때 **한 번만** 발급되어
`HlsDownloadRequest.playlistUrl`에 고정 저장된다. 이 토큰 자체가 서버에 의해 거부되면(401/403/410),
`HlsDownloadService`는 몇 번을 재시도해도 죽은 토큰으로만 요청하므로 절대 복구되지 않는다. 지금은
사용자가 검색 화면에서 그 영상 페이지를 수동으로 다시 열어 새 다운로드를 시작하는 수밖에 없다.

또한 다운로드 상태 화면(`DownloadStatusActivity`)에서, "일시적 오류로 N분 후 자동 재시도" 상태
(`HlsDownloadStatus.IDLE`)일 때 사용자가 즉시 재시도하거나 취소할 방법이 없다는 것도 이번에 확인됐다.

## 목표

- 재생목록 자체가 401/403/410으로 거부되면, 사람 개입 없이 헤드리스 WebView로 그 영상 페이지를 다시
  열어 새 토큰을 확보하고 다운로드를 이어간다.
- 다운로드 상태 화면에서 대기 중(IDLE, 자동 재시도 대기 포함)인 항목도 즉시 수동으로 "다시 시도"하거나
  "취소"할 수 있다.
- 취소는 항목별로만 하며, 전체 일괄 취소 UI는 제거한다.

## 비목표

- 네트워크 끊김/기기 재부팅/OS의 프로세스 강제 종료에 대한 복원력 개선 — 기존 동작(네트워크 끊김은
  이미 3회 백오프 재시도, 프로세스 종료 시 FAILED 처리) 그대로 유지. 별도 스펙으로 다룬다.
- 세그먼트 단위(개별 `.ts` 파일) 요청이 401/403/410으로 막히는 경우의 토큰 갱신 — 재생목록 자체가
  살아있는데 특정 세그먼트만 막히는 경우는 매우 드물고, 오탐 시 불필요한 헤드리스 WebView 실행 비용이
  크므로 이번 범위에서 제외한다.
- 순수 HTTP(비-WebView) 기반 재탐지 경로 — 이미 `SearchWebViewController.findPlaylistFromPage`가
  존재하지만, 실측 로그상 대상 사이트는 JS 실행 후에야 m3u8 링크가 네트워크 요청으로 드러나므로
  이번 자동 갱신에는 사용하지 않는다.

## 아키텍처 개요

`SearchWebViewController`에 내장된 "네트워크 요청 가로채기 + JS 플레이리스트 스캐너 주입" 로직을
`HlsPlaylistProbeSession`으로 추출해 임의의 `WebView`에 붙일 수 있게 만든다. 화면에 보이는 검색 탭과,
화면에 붙지 않는(headless) 재탐지용 WebView가 이 로직을 공유한다.

```
HlsPlaylistProbeSession(
    webView: WebView,
    pageUrl: String,
    onFound: (HlsProbeMatch, headers: Map<String, String>, cookie: String?) -> Unit,
    onTimeout: () -> Unit
)
```

- `SearchWebViewController`는 이 클래스를 자신의 WebView에 붙이는 얇은 래퍼로 리팩터링한다
  (기존 동작·UI 100% 동일하게 유지, 회귀 없음).
- 신규 `HlsTokenRefresher`가 이 클래스를 headless `WebView`에 붙여서 재사용한다.

```kotlin
class HlsTokenRefresher(private val context: Context) {
    /** Dispatchers.Main으로 hop, headless WebView 생성 → probe 세션 실행 → 정리.
     *  20초 내 못 찾으면 null. */
    suspend fun refresh(pageUrl: String): HlsProbeMatch?
}
```

## 데이터 흐름

```
runDownloadAttempt(request)
  └─ resolveMediaPlaylist(request)
       └─ fetchText(playlistUrl) → HTTP 401/403/410
            └─ HlsDownloadException(NOT_RETRYABLE, stage=PLAYLIST, httpCode)
                 └─ stage == PLAYLIST 이고 코드가 401/403/410 이면:
                      refreshAttempts < HlsTokenRefreshPolicy.maxAttempts (2) ?
                        ├─ Yes → HlsTokenRefresher.refresh(request.pageUrl)
                        │         ├─ 성공 → 새 playlistUrl/headers/cookie로 request 교체
                        │         │          → HlsDownloadStore에 즉시 저장(영속화)
                        │         │          → totalSegments 재확인 후 resolveMediaPlaylist 재시도
                        │         └─ 실패(타임아웃/미검출) → refreshAttempts++
                        │                    → 기존 백오프 지연 후 전체 재시도(재시도 시 다시 refresh부터)
                        └─ No  → 최종 FAILED
                                 ("사이트에서 새 접근 권한을 받지 못해 다운로드를 중단했습니다.
                                   페이지를 열어 다시 시도해 주세요.")
```

**세그먼트 이어받기 유지**: `downloadedSegments`/임시 파일(`tempTsFile`)은 토큰 갱신과 무관하게
그대로 유지한다. 단, 새로 받은 재생목록의 `totalSegments`가 기존과 다르면 화질/인코딩이 바뀐 것으로
간주해 임시 파일을 버리고 처음부터 다시 받는다.

## 컴포넌트별 변경

- **`HlsDownloadException`**: `stage: HlsDownloadStage` (`PLAYLIST` | `SEGMENT`) 필드 추가.
  `resolveMediaPlaylist`/`fetchText` 경로에서 던질 때는 `PLAYLIST`, `appendUrlTo`(세그먼트)에서
  던질 때는 `SEGMENT`로 설정.
- **`HlsTokenRefreshPolicy`** (신규, 순수 함수 object): `maxAttempts = 2`. 시도 가능 여부만 판단하는
  단순 카운터 정책 — 기존 `HlsDownloadRetryPolicy`와 동일한 패턴.
- **`HlsPlaylistProbeSession`** (신규, `SearchWebViewController`에서 추출): WebView 요청 가로채기 +
  JS 스캐너 주입 + 콜백. `SearchWebViewController`는 이를 사용하도록 리팩터링(동작 변화 없음).
- **`HlsTokenRefresher`** (신규): headless WebView 생성/정리, `HlsPlaylistProbeSession` 연결,
  타임아웃 처리.
- **`HlsDownloadService`**: `runDownloadAttempt`에서 `PLAYLIST` 단계 401/403/410 처리 분기 추가,
  갱신 성공 시 `HlsDownloadStore` 갱신 후 이어서 진행.
- **`HlsDownloadStore`**: 별도 메서드 불필요. 갱신된 `HlsDownloadRequest`를 담은 `HlsDownloadProgress`를
  기존 `update()`에 그대로 전달하면 된다 (`withResumableFieldsFrom`이 `request = request ?: previous.request`로
  동작하므로, 새 request가 채워져 있으면 그대로 덮어써짐 — 코드 확인 완료).

## 에러 처리 / 안전장치

- **타임아웃**: `withTimeoutOrNull(20_000)`. 실측 로그 기준 정상 탐지는 1~2초, 광고 스크립트 로딩 등
  변동성을 감안한 여유.
- **WebView 정리**: 성공/타임아웃/취소/예외 모든 경로에서 `finally`로 `destroy()` 보장 (메모리 누수
  방지).
- **동시성**: WebView 작업은 전부 `Dispatchers.Main`으로 직렬화되므로 여러 다운로드가 동시에 갱신을
  시도해도 순차 처리되어 별도 락이 필요 없다.
- **세그먼트 수 불일치**: 새 재생목록의 `totalSegments`가 기존과 다르면 임시 파일 폐기 후 재시작.

## UI 변경 (다운로드 상태 화면)

**현재 문제**: `DownloadStatusController.createActionRow()`는 `다시 시도`를 FAILED/CANCELED에서만,
`취소`를 `isRunning()`(FETCHING_PLAYLIST/DOWNLOADING/REMUXING)에서만 노출한다. `IDLE`(대기 중 —
자동 재시도 대기 포함) 상태는 어느 조건에도 해당하지 않아 **버튼이 전혀 뜨지 않는다.**

**변경**:
1. `IDLE` 상태에도 `다시 시도` + `취소` 버튼을 함께 노출한다.
2. **기존 버그 수정**: `HlsDownloadService.retryDownload()`가 `startDownload()`를 호출할 때, 이미
   백오프 대기 중인 코루틴이 `downloadJobs`에 남아있으면 `startDownload()` 진입부의
   `if (downloadJobs.containsKey(id)) return` 가드에 걸려 아무 동작도 하지 않는다. `retryDownload()`
   에서 `startDownload()` 호출 전에 `downloadJobs.remove(id)?.cancel()`로 대기 중인 job을 먼저
   취소하도록 수정한다.
3. 상단의 전체 취소 버튼(`btn_cancel_download`, "진행 중인 다운로드 취소")과 관련 로직
   (`render()`의 `btnCancel.visibility` 토글 포함)을 제거한다. 취소는 항목별 버튼으로만 수행한다.
4. `취소` 버튼은 빨간 배경 + 흰 글씨로 스타일을 분리한다 (`actionButton()`에 danger 변형 추가 또는
   별도 파라미터). `다시 시도`/`시청`/`가져오기`는 기존 스타일 유지.
5. **완료된 다운로드에 `삭제` 버튼 추가**: `시청`/`가져오기` 옆에 `삭제`(danger 스타일) 버튼을 추가한다.
   `MainActivity`의 기존 파일 삭제 확인 다이얼로그 관례(`MaterialAlertDialogBuilder`, "파일 삭제" /
   "「이름」을 삭제하시겠습니까? 이 작업은 되돌릴 수 없습니다.")를 그대로 따른다. 확인 시 출력 파일을
   삭제하고 `HlsDownloadStore.remove(id)`(신규 메서드)로 목록에서도 제거한다.

## 테스트 전략

- 순수 로직은 유닛 테스트로 커버 (기존 `HlsDownloadRetryPolicyTest.kt` 패턴과 동일):
  - `HlsTokenRefreshPolicy` 최대 시도 횟수 경계값
  - `stage` 기반 트리거 여부 판단 (PLAYLIST+401/403/410만 갱신 시도, SEGMENT는 미시도, 404는 미시도)
  - 세그먼트 수 불일치 시 재시작 판단 로직
- 실제 headless WebView의 JS 실행/네트워크 감지 자체는 유닛 테스트로 검증하기 어렵다 (Robolectric으로도
  실사이트 JS 동작 재현 불가 — 기존 `SearchWebViewController`의 실제 탐지 로직도 유닛 테스트 없음과
  동일한 상황). 기기에서 직접 재현해 `hls_download_history.json`/로그로 확인하는 방식으로 검증한다
  (Accept-Encoding 수정 검증 때와 동일한 방식).
- UI 변경(버튼 노출 조건, 재시도 버그 수정)은 `DownloadStatusController`에 대한 유닛 테스트가 현재
  없으므로, 기기에서 IDLE 상태를 재현해 버튼 노출 및 동작을 수동 확인한다.
