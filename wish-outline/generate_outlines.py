#!/usr/bin/env python3
"""Generate a requested number of profile-backed outline files."""

from __future__ import annotations

import argparse
from dataclasses import dataclass
from pathlib import Path
import sys
from typing import Any
import re

from profiles import get_common_arcs, get_profile


REPO_ROOT = Path(__file__).resolve().parent
CHARACTER_DIR = REPO_ROOT / "characters"
OUTLINE_DIR = REPO_ROOT / "outlines"


CHARACTER_ORDER = [
    "김민정",
    "노은화",
    "도하영",
    "문아영",
    "박다정",
    "박미현",
    "박세연",
    "서나윤",
    "서지수",
    "오유림",
    "유하린",
    "이주은",
    "이주희",
    "이채영",
    "이하은",
    "임세라",
    "차소연",
    "최유진",
    "최윤서",
    "한서진",
]


@dataclass(frozen=True)
class Character:
    name: str
    profile: str
    position: str
    speech: str
    personality: str
    appearance: str
    points: str


def section(text: str, heading: str) -> str:
    pattern = rf"## {re.escape(heading)}\n(.*?)(?=\n## |\Z)"
    match = re.search(pattern, text, flags=re.S)
    return match.group(1).strip() if match else ""


def bullet_value(text: str, label: str) -> str:
    match = re.search(rf"- {re.escape(label)}:\s*(.+)", text)
    return match.group(1).strip() if match else ""


def first_sentence(text: str) -> str:
    clean = re.sub(r"\s+", " ", text.strip())
    if not clean:
        return ""
    parts = re.split(r"(?<=[.!?])\s+|(?<=다\.)\s+", clean)
    return parts[0].strip()


def has_final_consonant(text: str) -> bool:
    if not text:
        return False
    code = ord(text[-1])
    if 0xAC00 <= code <= 0xD7A3:
        return bool((code - 0xAC00) % 28)
    return False


def object_particle(text: str) -> str:
    """Return a conservative object particle for a Korean phrase."""
    if has_final_consonant(text):
        return "을"
    return "를"


def subject_particle(text: str) -> str:
    """Return a conservative subject/topic particle for a Korean phrase."""
    if has_final_consonant(text):
        return "은"
    return "는"


def nominative_particle(text: str) -> str:
    """Return a conservative nominative particle for a Korean phrase."""
    if has_final_consonant(text):
        return "이"
    return "가"


def as_visual_sentence(fragment: str, fallback_suffix: str) -> str:
    fragment = fragment.strip()
    if fragment.endswith((".", "!", "?")):
        return fragment
    if fragment.endswith(("다", "있다", "준다", "된다", "만든다", "보인다", "남는다", "겹친다")):
        return fragment + "."
    return fragment + fallback_suffix


def pick(items: list[dict[str, str]] | list[str], ep: int, salt: int):
    return items[(ep * 7 + salt * 11) % len(items)]


def select_scene(ep: int, char: Character) -> dict[str, Any]:
    profile = get_profile(char.name)
    if not profile or "events" not in profile:
        raise ValueError(f"character JSON profile not found: {char.name}")

    character_index = (
        CHARACTER_ORDER.index(char.name) if char.name in CHARACTER_ORDER else 0
    )
    event = pick(profile["events"], ep, character_index)
    arc = pick(get_common_arcs(), ep, character_index + 7)

    return {
        "place": event["place"],
        "weather": event["weather"],
        "pressure": event["pressure"],
        "place_details": event["place_details"],
        "clothes": pick(event["outfit_pool"], ep, character_index + 13),
        "hair": pick(event["hair_pool"], ep, character_index + 19),
        "arc_type": arc["type"],
        "start": arc["start"],
        "turn": arc["turn"],
        "after": arc["after"],
        "profile_name": profile["name"],
        "event_id": event["id"],
        "event_set_id": event["id"],
    }


def load_characters() -> list[Character]:
    characters: list[Character] = []
    for name in CHARACTER_ORDER:
        path = CHARACTER_DIR / f"{name}.txt"
        profile = path.read_text(encoding="utf-8").strip()
        characters.append(
            Character(
                name=name,
                profile=profile,
                position=bullet_value(profile, "리부트 포지션"),
                speech=first_sentence(section(profile, "말투")),
                personality=first_sentence(section(profile, "성격")),
                appearance=first_sentence(section(profile, "외형")),
                points=section(profile, "장면 활용 포인트").replace("\n", " "),
            )
        )
    return characters


def positive_count(value: str) -> int:
    count = int(value)
    if count < 1:
        raise argparse.ArgumentTypeError("count must be a positive integer")
    return count


def parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Generate outline files using character JSON profiles."
    )
    parser.add_argument("count", type=positive_count, help="Number of outlines to generate.")
    parser.add_argument("--character", help="Use one JSON-profiled character only.")
    return parser.parse_args(argv)


def profiled_characters(
    characters: list[Character],
    character_name: str | None = None,
) -> list[Character]:
    available = [character for character in characters if get_profile(character.name)]
    if character_name is None:
        if not available:
            raise ValueError("no character JSON profiles found")
        return available

    selected = [character for character in available if character.name == character_name]
    if not selected:
        raise ValueError(f"character JSON profile not found: {character_name}")
    return selected


def outline_text(ep: int, char: Character, scene: dict[str, Any]) -> str:
    title = f"[{ep}화 성인씬 개요]"
    speech = char.speech or "가까워질수록 말투의 온도가 달라진다."
    personality = char.personality or "상대의 반응을 세심하게 살핀다."
    appearance = char.appearance or f"{char.name}은 장면 안에서 선명한 인상을 남기는 인물이다."
    points = char.points or char.position

    place_obj = f"{scene['place']}{object_particle(scene['place'])}"
    name_topic = f"{char.name}{subject_particle(char.name)}"
    name_nom = f"{char.name}{nominative_particle(char.name)}"
    visual_clothes = as_visual_sentence(scene["clothes"], " 차림이다.")
    visual_hair = as_visual_sentence(scene["hair"], " 상태다.")
    place_details = scene.get("place_details") or []
    place_detail_line = (
        f"- 장소 디테일: {', '.join(place_details)}.\n" if place_details else ""
    )

    return f"""{title}

이미지 프롬프트:
2026년 여름, {place_obj} 배경으로 한 은밀한 영화 스틸. {appearance} {name_topic} {visual_clothes} 헤어는 {visual_hair} 장소의 공기감은 {scene['weather']}. 카메라는 노골적인 노출이나 행위가 아니라, 표정과 시선, 젖은 바닥이나 낮은 조명, 잠시 멈춘 자세가 만드는 긴장을 포착한다.

인물:
- 김용식
- {char.name}

여성 캐릭터 전체 프로필:

{char.profile}

시기:
- 2026년 여름.
- {scene['weather']}.

장소:
- {scene['place']}.
- {scene['pressure']}.
{place_detail_line}\
- 장면은 외부 시선이 줄어든 시간대와 좁아진 동선을 활용해, 두 사람이 같은 공간에 남는 선택을 선명하게 만든다.

이번 씬 복장:
- {name_topic} {scene['clothes']}.
- 헤어는 {scene['hair']}.
- 캐릭터 고유 분위기는 `{points}`의 소품과 동선을 일부 끌어와 살린다.
- 용식은 여름용 셔츠나 얇은 재킷 차림으로, 비나 열기 때문에 평소보다 느슨한 인상을 준다.

관계 구도:
- {name_topic} {personality}
- 말투는 {speech}
- 이 화의 핵심은 연애 고백보다, 서로가 이미 선택한 분위기를 더는 모른 척하지 못하는 데 있다.
- {scene['start']}.

장면 톤:
- 섹스가 중심이 되는 독립 장면 시작 방식, 금기감, 주도권 변화, 사후 반응을 중심으로 잡는다.
- 장소와 날씨가 둘의 퇴로를 줄이고, 헤어와 복장의 작은 흐트러짐이 평소 이미지가 깨지는 순간을 보여준다.
- {char.name}의 캐릭터성은 말투, 시선, 거리 조절, 끝난 뒤의 태도에서 드러난다.

장면 목적:
- {ep}화의 목적은 {char.name}의 고유한 성격과 직업적 얼굴이 사적인 욕망 앞에서 어떻게 바뀌는지 보여주는 것이다.
- {scene['place']}의 압력과 {scene['weather']}의 감각을 이용해, 두 사람이 짧은 시간 안에 관계의 방향을 선택하게 만든다.

도입:
- 용식은 {scene['place']}에서 {char.name}과 마주친다.
- 처음 대화는 사소하고 현실적인 이유에서 시작된다. 비, 늦은 시간, 닫힌 문, 남은 일, 기다리는 차 같은 요소가 둘을 조금 더 머물게 한다.
- {name_topic} 평소의 말투와 태도를 유지하려 하지만, 헤어와 복장의 작은 변화 때문에 이미 사적인 얼굴이 드러난다.
- {scene['start']}.

관계 전환:
- {scene['turn']}.

다음에 남는 감정:
- {scene['after']}.
- {name_topic} 평소의 얼굴로 돌아가려 하지만, 작은 물건이나 메시지, 다음 약속의 핑계가 남는다.
- 그 여자는 자신이 완전히 망가졌다는 걸 안다. 남자의 폭풍 같은 섹스에 몸이 남김없이 부서졌고, 하체는 아직도 후들거리며 제대로 서 있기도 힘들다. 체액과 정액은 흔적이 남아있고, 다리는 떨리고, 속은 텅 비어 있는데도 그 감각이 너무 강렬해서 도저히 잊을 수가 없다. 몸이 기억한다. 그가 얼마나 깊게, 거칠게, 집요하게 파고들었는지를. 망가진 만큼, 그 쾌감도 컸기에 다음 만남을 피하기는커녕 오히려 그 폭풍을 다시 견디고 싶어 안달이 나 버린다.
"""


def generate_outlines(
    count: int,
    character_name: str | None = None,
    output_dir: Path = OUTLINE_DIR,
) -> list[Path]:
    characters = profiled_characters(load_characters(), character_name)
    output_dir.mkdir(parents=True, exist_ok=True)
    written: list[Path] = []
    for ep in range(1, count + 1):
        char = characters[(ep - 1) % len(characters)]
        scene = select_scene(ep, char)
        path = output_dir / f"{ep:03d}화.txt"
        path.write_text(outline_text(ep, char, scene), encoding="utf-8")
        written.append(path)
    return written


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv if argv is not None else sys.argv[1:])
    try:
        written = generate_outlines(args.count, args.character)
    except ValueError as error:
        raise SystemExit(str(error)) from error

    print(
        f"Generated {len(written)} outline files: "
        f"{written[0].name} - {written[-1].name}."
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
