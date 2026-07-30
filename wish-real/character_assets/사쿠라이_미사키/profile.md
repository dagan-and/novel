# 사쿠라이 미사키 캐릭터 이미지 기준

## 목적

사쿠라이 미사키의 삽화 일관성을 유지하기 위한 이미지 참조 폴더다.
소설 삽화 생성 시 `characters/사쿠라이_미사키.md`의 고정 설정과 이 폴더의 기준 이미지, 프롬프트를 함께 참고한다.

## 기준 이미지

- `references/main.png`: 삽화 생성 시 우선 참고하는 매력 보정 기준 이미지.
- `references/originals/flower-crown-main.png`: 화관을 쓴 원본 기준 이미지. 얼굴형, 미소, 전체 인상의 1순위 기준이다.
- `references/originals/back-fullbody.png`: 뒤태, 키 비율, 가늘고 여성스러운 실루엣 참고.
- `references/originals/soft-glasses.jpg`: 부드러운 분위기 참고.
- `references/originals/attractiveness-smile.webp`: 미소, 눈매, 밝고 사랑스러운 보정 강도 참고. 특정 인물을 그대로 복제하지 않는다.
- `references/originals/attractiveness-calm.webp`: 차분한 눈매, 정돈된 인상, 성숙한 매력 보정 강도 참고. 특정 인물을 그대로 복제하지 않는다.

## 사용 우선순위

1. `characters/사쿠라이_미사키.md`의 확정 외형과 성격
2. `references/main.png`
3. `references/originals/flower-crown-main.png`
4. `references/originals/back-fullbody.png`
5. 장면 분위기에 따라 `soft-glasses.jpg`, `attractiveness-smile.webp`, `attractiveness-calm.webp`
6. `prompts/base_prompt.md`
7. `prompts/negative_prompt.md`

화관 사진은 미사키의 실제 인상과 얼굴 계열의 중심이다.
뒤의 매력 참고 이미지는 얼굴을 복제하는 용도가 아니라, 눈매, 미소, 정돈된 피부 표현, 세련된 분위기의 보정 강도를 잡는 용도로만 사용한다.

## 고정 인상

- 일본 여성, 1999년생, 가나자와 출신.
- 작고 섬세한 타원형 얼굴.
- 부드러운 눈매와 친근한 미소.
- 자연스러운 검정 또는 짙은 갈색 긴 머리.
- 화려한 미인보다 맑고 단정하며 사랑스러운 인상.
- 가늘고 균형 잡힌 체형 안에 부드러운 여성적 곡선이 있다.
- 성숙한 여성의 부드러운 매력을 유지하되, 지나친 노출과 과장된 신체 비율은 피한다.

