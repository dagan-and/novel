# TestFileView / VideoManager

Android(Kotlin)로 작성된 로컬 동영상 관리 앱입니다. 이 저장소의 실제 빌드 대상은 루트의 `app` 모듈 하나입니다.

## 프로젝트 구조

```text
.
├── app/                         # 실제 Android 앱 모듈
│   └── src/main/java/com/kys/videomanager/
│       ├── MainActivity.kt       # 화면, 영상 로딩, 필터, 삭제, 플레이어 실행
│       ├── VideoAdapter.kt       # RecyclerView 어댑터와 썸네일/별점 UI
│       ├── VideoFilter.kt        # 별점 필터 순수 로직
│       ├── VideoItem.kt          # 영상 데이터 모델
│       ├── VideoPreferenceManager.kt
│       └── RatingBackupManager.kt
├── docs/superpowers/            # 기능 구현 계획/설계 문서
├── gradle/                      # Gradle wrapper 설정
├── settings.gradle.kts          # include(":app")
└── build.gradle.kts             # 루트 Gradle 설정
```

## 주요 기능

- 앱 전용 외부 저장소의 `videos` 폴더에서 영상 파일 스캔
- RecyclerView 영상 목록 표시
- MediaMetadataRetriever 기반 재생 시간/썸네일 추출
- 별점 저장, 별점순 정렬, 별점 필터
- 기본 동영상 플레이어 선택/초기화
- 롱클릭 파일 삭제
- 별점/기본 플레이어 설정을 Downloads 백업 JSON으로 내보내기/복원

## 빌드와 테스트

```bash
./gradlew :app:testDebugUnitTest --no-daemon
./gradlew :app:assembleDebug --no-daemon
```

## 릴리즈 APK

설치 가능한 릴리즈 APK는 아래 명령으로 만든다.

```bash
./scripts/build_release.sh
```

서명 설정과 수동 명령은 [RELEASE_BUILD.md](/Users/kys1207/AndroidStudioProjects/VideoManager/RELEASE_BUILD.md)에 기록되어 있다. 현재 릴리즈 빌드는 `MyHome` 키스토어 설정을 fallback으로 사용한다.

## 참고

이전에 존재하던 `VideoManagerApp/` 폴더는 루트 `app/`과 중복된 오래된 복사본이었고, Gradle 빌드에도 포함되지 않아 제거했습니다. 앞으로 앱 코드는 `app/` 아래만 수정하면 됩니다.
