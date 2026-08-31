# 생체 인증 + PIN 폴백 + 분실 복구 설계

## 배경

`MainActivity.authenticateBeforeOpening()`은 현재 생체 인증만 지원한다. `BiometricManager.canAuthenticate()`가
성공을 반환하지 않으면(하드웨어 없음, 등록된 생체정보 없음 등) "지문 인증을 사용할 수 없어 앱을 열 수
없습니다" 토스트만 띄우고 앱을 그냥 종료해버린다 — 그런 기기에서는 앱을 아예 못 쓴다. 생체 인증이
가능한 기기에서도 대체 수단이 전혀 없다.

이 앱은 서버/계정 시스템이 없는 개인용 앱이라, PIN을 잊었을 때 흔한 "가입 이메일로 인증 링크 발송" 같은
복구는 애초에 만들 수 없다.

## 목표

- 생체 인증을 우선 시도하고, 생체 인증이 불가능한 기기이거나 사용자가 원하면 4자리 PIN으로 잠금해제.
- PIN 미설정 상태(생체 인증 불가 기기의 최초 실행 등)에서는 PIN 설정을 강제.
- 서버 없이도, 개발자가 이메일로 받은 값을 수동으로 계산해 답장하는 방식으로 PIN 분실 시 복구 가능하게.
- 최근 앱 화면/스크린샷에서 앱 내용이 노출되지 않게 처리.

## 비목표

- 생체/PIN 연속 실패에 대한 잠금·지연 등 브루트포스 방지 장치. (4자리 PIN 자체가 이미 약한 방어이긴
  하나, 이번 스펙 범위 밖 — 필요해지면 별도 스펙.)
- 서버 기반 계정/이메일 인증 시스템. 이메일 발송/수신 자동화는 하지 않는다 — 사용자가 기기 고유 코드를
  직접 이메일로 보내고, 개발자가 계산기(스크립트)로 코드를 계산해 수동으로 답장하는 것을 전제로 한다.
- 잠금 해제 후 설정 화면에서 PIN을 임의로 변경하는 메뉴. 이번 스펙은 "최초 설정"과 "분실 후 재설정"
  흐름만 다룬다.
- 별도 Activity/화면 전환. 기존 앱의 다이얼로그 기반 상호작용 방식(별점 입력, 파일 삭제 확인, 가져오기
  옵션 등과 동일)을 그대로 따른다.

## 아키텍처 개요

새 패키지 `security`에 순수 로직 위주의 파일 3개를 추가하고, `MainActivity`에 다이얼로그 4개(PIN 입력 /
최초 PIN 설정 / PIN 찾기 / 새 PIN 설정)를 추가해 기존 `authenticateBeforeOpening()`을 확장한다. 새
Activity나 레이아웃 파일은 만들지 않는다.

```
security/
  DeviceIdentity.kt        기기별 고유 코드 생성/영구 저장
  RecoveryCodePolicy.kt    고유 코드 → 4자리 복구 코드 (순수 함수, HMAC-SHA256)
  PinPreferenceManager.kt  PIN 해시 저장/검증 (SHA-256, 기기 고유 코드를 salt로 사용)
```

## 데이터 흐름

```
MainActivity.authenticateBeforeOpening()
 └─ BiometricManager.canAuthenticate() == SUCCESS ?
      ├─ 아니오 → showPinFlow()
      └─ 예 → BiometricPrompt 표시 (부정 버튼 텍스트 = "PIN으로 입력")
              ├─ 인증 성공 → openUnlockedApp()
              ├─ 부정 버튼("PIN으로 입력") 클릭 → showPinFlow()
              └─ 그 외 에러(취소, 잠김 등) → 기존과 동일하게 Toast + finish()

showPinFlow()
 └─ PinPreferenceManager.hasPin() ?
      ├─ 아니오 → showPinSetupDialog() (최초 설정, 강제)
      └─ 예 → showPinEntryDialog()
               ├─ 정답 → openUnlockedApp()
               ├─ 오답 → Toast, 다이얼로그 유지(재입력)
               └─ "PIN 찾기" 버튼 → showPinRecoveryDialog()

showPinRecoveryDialog()
 └─ DeviceIdentity.getOrCreateId() 표시 + "이메일로 문의" 버튼(mailto: 인텐트, 본문에 고유 코드 자동 삽입)
    + 4자리 코드 입력란
      ├─ 입력값 == RecoveryCodePolicy.computeResetCode(deviceId) → showNewPinDialog()
      └─ 불일치 → Toast, 다이얼로그 유지

showPinSetupDialog() / showNewPinDialog()
 └─ 새 PIN + 확인용 재입력 → 둘 다 4자리 숫자이고 서로 일치해야 저장
      └─ PinPreferenceManager.savePin(pin, deviceId) → openUnlockedApp()
```

## 컴포넌트별 상세

- **`DeviceIdentity`**: `init(context)` + SharedPreferences 싱글톤(`VideoPreferenceManager`와 동일 패턴).
  `getOrCreateId(): String` — 이미 저장된 값이 있으면 그대로 반환, 없으면 13자리 고유 코드를 생성해
  저장 후 반환. 재설치 전까지 불변. **생성 규칙(중요)**: `RecoveryCodePolicy`가 항상 계산 가능해야
  하므로, A~J 알파벳 중 무작위 4글자를 먼저 뽑고(이것이 실제 복구 코드로 변환되는 부분), 나머지
  9자리는 K~Z 알파벳과 0~9 숫자 중에서만 무작위로 채운다(디코이 — A~J를 포함하지 않아 복구 코드
  계산에 영향을 주지 않음). 이 4글자 + 9글자를 무작위로 섞어서 최종 코드를 만든다. 이렇게 하면
  생성되는 모든 고유 코드에 A~J 문자가 정확히 4개만 포함되는 것이 보장된다.
- **`RecoveryCodePolicy`**: 순수 함수 `object`. `computeResetCode(deviceId: String): String?` — 고유
  코드 문자열에서 A~J에 해당하는 문자만 순서대로 추출해, 각각을 아래 표대로 숫자로 바꿔 이어붙인
  4자리 문자열을 반환한다(4개 미만이면 `null` — `DeviceIdentity`가 항상 4개를 보장하므로 정상 흐름에서는
  발생하지 않는다).

  | 문자 | A | B | C | D | E | F | G | H | I | J |
  |---|---|---|---|---|---|---|---|---|---|---|
  | 숫자 | 0 | 1 | 2 | 3 | 4 | 5 | 6 | 7 | 8 | 9 |

  예: `FG1238AA88NZXZ` → A~J 문자만 순서대로 뽑으면 F, G, A, A → 5, 6, 0, 0 → `"5600"`.
  암호화나 비밀 키 없이 고정된 치환표만 쓰므로, 개발자가 표를 외워서 암산으로도 계산할 수 있을 만큼
  단순하다 — 그래도 편의상 스크립트는 만들어 둔다. 사용자가 자기 고유 코드를 봐도 어떤 문자가 실제
  코드에 쓰이는지, 나머지가 의미 없는 디코이인지 구분할 단서가 없어서 눈으로 유추하긴 어렵다.
- **`PinPreferenceManager`**: `init(context)` + SharedPreferences 싱글톤. `hasPin(): Boolean`,
  `savePin(pin: String, salt: String)`, `verifyPin(pin: String, salt: String): Boolean`. PIN은 평문
  저장하지 않고 `hashPin(pin, salt)`(파일 내 top-level 순수 함수, SHA-256 hex)의 결과만 저장한다. salt로는
  `DeviceIdentity.getOrCreateId()`를 사용해 별도 salt 저장 없이 재사용한다.
- **`MainActivity`**: `authenticateBeforeOpening()` 수정(위 데이터 흐름대로), `showPinFlow()`/
  `showPinEntryDialog()`/`showPinSetupDialog()`/`showPinRecoveryDialog()`/`showNewPinDialog()` 5개
  private 메서드 추가. 다이얼로그는 기존 코드의 `MaterialAlertDialogBuilder` + 커스텀 `LinearLayout`
  콘텐츠 패턴(`showImportOptions`, `confirmAndDelete` 등)을 그대로 따른다. 오답 시 다이얼로그를 자동으로
  닫지 않아야 하므로, `setPositiveButton`으로 등록하지 않고 `.show()` 후 `dialog.getButton(BUTTON_POSITIVE)
  .setOnClickListener { ... }`로 직접 제어한다(이미 `showImportProgressDialog`에서 쓰는 방식과 동일).
- **화면 보안**: `MainActivity.onCreate()` 최상단(super 호출 직후)에
  `window.setFlags(WindowManager.LayoutParams.FLAG_SECURE, WindowManager.LayoutParams.FLAG_SECURE)`
  추가 — 최근 앱 목록 썸네일과 스크린샷 캡처에서 이 액티비티의 모든 화면(잠금 화면 포함)이 가려진다.
- **개발자용 계산 스크립트**: `scripts/compute_pin_reset_code.py` — `RecoveryCodePolicy`와 동일한
  A~J 치환표 로직을 순수 Python으로 재구현. 사용자가 이메일로 보낸 고유 코드를 인자로 실행하면 4자리
  복구 코드를 출력한다. 비밀 키가 없는 고정 치환표라 앱 코드가 바뀔 일이 없고, 스크립트도 한 번 만들면
  계속 그대로 쓸 수 있다.

## 에러 처리

- 생체 인증도 PIN도 다 실패/취소 → 기존과 동일하게 Toast + `finish()`. 콘텐츠 노출 없음.
- 복구 코드 입력이 계속 틀려도 별도 잠금 없이 재시도 가능(비목표에서 언급한 대로 브루트포스 방지는
  범위 밖 — 4자리 코드 자체가 이미 약한 보호이므로, 이 앱의 위협 모델(개인 기기, 낮은 가치 타깃)에서는
  허용 가능한 수준으로 판단).
- PIN 설정/새 PIN 설정 시 두 입력값이 4자리 숫자가 아니거나 서로 불일치하면 저장하지 않고 Toast로 안내.

## 테스트 전략

- `RecoveryCodePolicyTest`: 고정된 device ID 문자열 몇 개에 대해 기대되는 4자리 코드를 하드코딩해
  검증(결정적 함수이므로 가능). 서로 다른 입력이면 다른 코드가 나오는지도 확인.
- `hashPin` 순수 함수 테스트: 같은 pin+salt → 같은 해시, 다른 pin 또는 다른 salt → 다른 해시, 평문 PIN이
  해시 문자열에 그대로 노출되지 않는지 확인.
- `DeviceIdentity`, `PinPreferenceManager`의 SharedPreferences 연동 부분과 `MainActivity`의 다이얼로그
  UI는 이 프로젝트 기존 관례대로(생체 인증/Firebase 연동 클래스들과 동일) 단위테스트 대상에서 제외하고
  기기에서 수동으로 확인한다.
