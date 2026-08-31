# Firebase Remote Config 강제 업데이트 설계

## 배경

앱에 현재 원격 killswitch/강제 업데이트 수단이 전혀 없다. 문제가 있는 빌드를 배포한 뒤에도
사용자가 스스로 업데이트하기 전까지는 막을 방법이 없다. `google-services` 플러그인과
`google-services.json`은 이미 Firebase App Distribution 용도로 붙어 있어 Firebase 프로젝트
자체는 존재하지만, Remote Config SDK는 아직 의존성에 없다.

## 목표

- 앱 실행 시 Firebase Remote Config를 조회해, 현재 설치된 버전이 최소 지원 버전보다 낮으면
  잠금 해제(생체/PIN) 이전에 강제로 업데이트 화면으로 막는다.
- 서버 쪽 설정(Remote Config 콘솔)만 바꾸면 앱 코드 수정/재배포 없이 강제 업데이트를 켜고 끌 수 있다.
- Remote Config 조회 자체가 실패해도(오프라인, Firebase 장애 등) 앱을 못 쓰게 만들지 않는다
  (fail-open).

## 비목표

- 강제 업데이트 외의 범용 원격 설정(기능 플래그, A/B 테스트 등) — 이번 스펙은 버전 게이팅 하나만
  다룬다. 같은 Remote Config 인스턴스를 나중에 다른 용도로 확장하는 것은 별도 스펙.
- 인앱 업데이트(Play Core In-App Update API) — 이번에는 Play 스토어 페이지로 이동시키는 것까지만
  다루고, 앱 안에서 다운로드/설치하는 흐름은 범위 밖.
- 마이너 업데이트(선택적 업데이트) 안내 — 이번 스펙은 "강제 차단" 한 가지 동작만 다룬다.

## 아키텍처 개요

기존 코드베이스의 `*Policy.resolve()` 순수 함수 패턴(`VideoImportPolicy`, `HlsDownloadOutputPolicy`,
`HlsTokenRefreshPolicy` 등)을 그대로 따른다. Firebase SDK 호출부와 차단 여부 판단 로직을 분리해서,
판단 로직만 유닛 테스트로 완전히 커버한다.

```
ForceUpdatePolicy.resolve(
    currentVersionCode: Int,
    minSupportedVersionCode: Long
): ForceUpdateDecision   // ALLOW | BLOCK

ForceUpdateGate(context: Context) {
    suspend fun check(currentVersionCode: Int): ForceUpdateResult
    // ForceUpdateResult(decision: ForceUpdateDecision, updateUrl: String, message: String)
}
```

- `ForceUpdatePolicy`는 Firebase와 완전히 무관한 순수 함수 — 버전 숫자 비교만 한다.
- `ForceUpdateGate`가 실제 Firebase Remote Config SDK(`fetchAndActivate()`)를 호출하고, 그 결과값을
  `ForceUpdatePolicy.resolve()`에 넘긴 뒤 `update_url`/`update_message` 값과 함께 결과를 묶어 반환한다.
- 조회 실패(타임아웃/네트워크 없음/예외) 시 `ForceUpdateGate`는 Firebase를 거치지 않고 즉시
  `ForceUpdateDecision.ALLOW`를 반환한다 (fail-open).

## 데이터 흐름

```
MainActivity.onCreate()
  └─ checkForceUpdate()  (코루틴)
       └─ ForceUpdateGate.check(BuildConfig.VERSION_CODE)
            ├─ Remote Config fetchAndActivate() 성공
            │    └─ ForceUpdatePolicy.resolve(VERSION_CODE, min_supported_version_code)
            │         ├─ ALLOW → authenticateBeforeOpening() 진행 (기존 흐름)
            │         └─ BLOCK → showForceUpdateDialog(update_url, update_message)
            │                     (뒤로가기 무효화, "업데이트" 버튼만 동작 → Play 스토어 이동 → finish())
            └─ 조회 실패(타임아웃/예외)
                 └─ ALLOW로 간주 → authenticateBeforeOpening() 진행
```

강제 업데이트 검사가 생체/PIN 인증보다 먼저 실행된다 — 구버전 사용자가 암호화된 콘텐츠 화면을
전혀 보지 못하게 막는 것이 목적이므로, 인증 프롬프트 자체를 아예 띄우지 않는다.

## Remote Config 키

| 키 | 타입 | 기본값(코드 내 setDefaultsAsync) | 설명 |
|---|---|---|---|
| `min_supported_version_code` | Long | 현재 `BuildConfig.VERSION_CODE`와 동일 | 이 값보다 작은 versionCode는 차단 |
| `update_url` | String | `https://play.google.com/store/apps/details?id=com.kys.videomanager` | 업데이트 버튼이 여는 링크 |
| `update_message` | String | `"새 버전이 있습니다. 업데이트 후 이용해 주세요."` | 다이얼로그 안내 문구 |

로컬 기본값을 현재 versionCode와 동일하게 심어두면, Remote Config를 아직 한 번도 fetch하지 못한
상태(최초 실행, 캐시 없음)에서도 `min_supported_version_code`가 0으로 남아 있다가 실수로 차단되는
일이 없다.

### 운영 시 주의사항 (콘솔 설정, 코드 변경 아님)

- **이 Firebase 프로젝트(`test1-1f100`)는 `com.kys.myhome` 앱도 함께 등록돼 있다.** Remote Config
  파라미터는 프로젝트 단위이지 앱 단위가 아니므로, 콘솔에서 위 세 파라미터에 `app.id ==
  '<videomanager app id>'` 조건을 반드시 걸어야 한다. 조건 없이 값을 바꾸면 같은 프로젝트의 다른 앱도
  같이 영향을 받는다.
- **`update_url` 기본값(Play 스토어 링크)은 아직 유효하지 않을 수 있다.** 이 앱은 현재 사이드로드/
  Firebase App Distribution으로만 배포 중이고(`AndroidManifest.xml` 주석 참고) Play 스토어에 등록되지
  않았다. `min_supported_version_code`를 실제로 올려서 강제 업데이트를 발동시키기 전에, 콘솔에서
  `update_url`을 실제로 열리는 주소(App Distribution 링크 등)로 먼저 설정해 둬야 한다 — 그렇지 않으면
  사용자는 차단된 채 "업데이트" 버튼을 눌러도 존재하지 않는 Play 스토어 페이지로 이동하게 된다.

## 컴포넌트별 변경

- **`ForceUpdateDecision`** (신규, enum): `ALLOW`, `BLOCK`.
- **`ForceUpdatePolicy`** (신규, 순수 함수 object): `resolve(currentVersionCode, minSupportedVersionCode)`.
  `currentVersionCode < minSupportedVersionCode`면 `BLOCK`, 아니면 `ALLOW`.
- **`ForceUpdateResult`** (신규, data class): `decision`, `updateUrl`, `message`.
- **`ForceUpdateGate`** (신규): Firebase Remote Config 초기화(`remoteConfigSettings { minimumFetchIntervalInSeconds = 3600 }`),
  `setDefaultsAsync(...)`, `fetchAndActivate()` 호출 및 예외 처리, 결과값을 `ForceUpdateResult`로 변환.
- **`MainActivity`**: `onCreate()`에서 `authenticateBeforeOpening()` 호출 전에 `checkForceUpdate()`를
  먼저 실행하도록 변경. `BLOCK`이면 닫을 수 없는 `AlertDialog`(뒤로가기도 `isEnabled = false` 콜백으로
  무효화, "업데이트" 버튼만 `Intent(ACTION_VIEW, Uri.parse(updateUrl))` 실행 후 `finish()`)를 띄운다.
- **`app/build.gradle`**: `implementation platform('com.google.firebase:firebase-bom:...')` +
  `implementation 'com.google.firebase:firebase-config'` 추가.

## 에러 처리 / 안전장치

- **fetch 실패(네트워크 없음/타임아웃/Firebase 장애)**: `ForceUpdateGate.check()`가 예외를 잡아
  `ALLOW`로 처리 — 인증 흐름을 그대로 진행시킨다. 앱이 Firebase 장애로 먹통이 되는 사태를 방지.
- **`setDefaultsAsync` 자체가 실패해도** SDK의 타입 기본값(Long 0)이 적용되므로
  `currentVersionCode < 0`은 항상 거짓 → 결과적으로 항상 통과.
- **다이얼로그는 `setCancelable(false)`** + 기기 뒤로가기 버튼도 `OnBackPressedCallback`으로 무효화 —
  강제 업데이트 상태에서는 어떤 경로로도 잠금 해제 화면에 도달할 수 없어야 한다.

## 테스트 전략

- `ForceUpdatePolicyTest` — 순수 함수라 완전히 유닛 테스트로 커버:
  - 현재 버전 == 최소 버전 → ALLOW
  - 현재 버전 > 최소 버전 → ALLOW
  - 현재 버전 < 최소 버전 → BLOCK
  - 최소 버전 0(기본값, 한 번도 fetch 안 됨) → 항상 ALLOW
- `ForceUpdateGate`는 Firebase SDK에 직접 의존하므로 (다른 `*Manager`/`*Service` 클래스들과 동일하게)
  유닛 테스트 대상에서 제외 — 실제 기기에서 Remote Config 콘솔 값을 바꿔가며 수동 확인.
- UI(다이얼로그 차단/뒤로가기 무효화)도 같은 이유로 기기에서 수동 확인.
