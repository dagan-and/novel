#!/usr/bin/env python3
"""Generate a requested number of profile-backed outline files."""

from __future__ import annotations

import argparse
from dataclasses import dataclass
from pathlib import Path
import subprocess
import sys
from typing import Any
import re
import random
import unicodedata
from urllib.parse import quote

from profiles import get_common_scene_config


REPO_ROOT = Path(__file__).resolve().parent
CHARACTER_DIR = REPO_ROOT / "characters"
OUTLINE_DIR = REPO_ROOT / "outlines"
IMAGE_EXTENSIONS = {".jpg", ".jpeg", ".png", ".webp"}


def character_profile_paths() -> list[Path]:
    paths: dict[str, Path] = {}

    for path in CHARACTER_DIR.glob("*.txt"):
        if path.is_file():
            paths[unicodedata.normalize("NFC", path.stem)] = path

    folders = CHARACTER_DIR.iterdir() if CHARACTER_DIR.exists() else []
    for folder in folders:
        if not folder.is_dir():
            continue
        profile_path = folder / f"{folder.name}.txt"
        if not profile_path.is_file():
            txt_files = sorted(path for path in folder.glob("*.txt") if path.is_file())
            if not txt_files:
                continue
            profile_path = txt_files[0]
        paths[unicodedata.normalize("NFC", profile_path.stem)] = profile_path

    return [paths[name] for name in sorted(paths)]


def character_names() -> list[str]:
    return [unicodedata.normalize("NFC", path.stem) for path in character_profile_paths()]


CHARACTER_ORDER = character_names()


@dataclass(frozen=True)
class Character:
    name: str
    profile: str
    position: str
    body_type: str
    speech: str
    personality: str
    appearance: str
    points: str
    image_links: list[str]


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


def compact_whitespace(text: str) -> str:
    return re.sub(r"\s+", " ", text.strip())


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


def outfit_pool_for(char: Character, outfits: dict[str, Any]) -> dict[str, list[str]]:
    outfit_pool = outfits.get(char.body_type)
    if outfit_pool is None:
        raise ValueError(
            f"unsupported character body type: {char.name}: {char.body_type}"
        )
    return outfit_pool


def git_output(args: list[str], repo_root: Path = REPO_ROOT) -> str:
    result = subprocess.run(
        ["git", *args],
        cwd=repo_root,
        text=True,
        capture_output=True,
        check=True,
    )
    return result.stdout.strip()


def github_repo_slug(remote_url: str) -> str | None:
    remote_url = remote_url.strip()
    if remote_url.startswith("git@github.com:"):
        slug = remote_url.removeprefix("git@github.com:")
    elif remote_url.startswith("https://github.com/"):
        slug = remote_url.removeprefix("https://github.com/")
    else:
        return None
    return slug.removesuffix(".git").strip("/") or None


def github_blob_base(repo_root: Path = REPO_ROOT) -> str | None:
    try:
        remote_url = git_output(["config", "--get", "remote.origin.url"], repo_root)
        branch = git_output(["branch", "--show-current"], repo_root)
    except (subprocess.CalledProcessError, FileNotFoundError):
        return None

    slug = github_repo_slug(remote_url)
    if not slug or not branch:
        return None
    return f"https://github.com/{slug}/blob/{branch}"


def git_relative_path(path: Path, repo_root: Path = REPO_ROOT) -> Path:
    try:
        tracked = git_output(
            [
                "-c",
                "core.quotePath=false",
                "ls-files",
                "--full-name",
                "--",
                str(path),
            ],
            repo_root,
        )
    except (subprocess.CalledProcessError, FileNotFoundError):
        tracked = ""
    if tracked:
        return Path(tracked.splitlines()[0])

    try:
        top_level = Path(git_output(["rev-parse", "--show-toplevel"], repo_root))
    except (subprocess.CalledProcessError, FileNotFoundError):
        top_level = repo_root
    relative = path.resolve().relative_to(top_level.resolve())
    return Path(unicodedata.normalize("NFC", relative.as_posix()))


def github_image_link(path: Path, repo_root: Path = REPO_ROOT) -> str | None:
    base = github_blob_base(repo_root)
    if not base:
        return None
    relative = git_relative_path(path, repo_root)
    return f"{base}/{quote(relative.as_posix(), safe='/')}"


def character_image_links(profile_path: Path) -> list[str]:
    links: list[str] = []
    for path in sorted(profile_path.parent.iterdir()):
        if not path.is_file() or path.suffix.lower() not in IMAGE_EXTENSIONS:
            continue
        link = github_image_link(path)
        if link:
            links.append(link)
    return links


def location_driven_arc(char: Character, place: str) -> dict[str, str]:
    return {
        "type": "location_driven",
        "start": f"{place}에서 외부 시선이 줄어든 틈에 현실적인 대화가 시작된다",
        "turn": (
            f"{char.name}의 성격과 말투를 유지한 채 두 사람 사이의 거리와 "
            "주도권이 달라진다"
        ),
        "after": "장면이 끝난 뒤에도 다음 만남으로 이어질 감정과 작은 단서가 남는다",
    }


def select_arousal_elements(
    location: dict[str, Any],
) -> list[dict[str, Any]]:
    """Return every arousal element configured for the selected location."""
    elements = location.get("arousal_elements") or []
    return [dict(element) for element in elements]


def select_entry_approach(
    location: dict[str, Any],
    rng: random.Random,
    recent_approaches: dict[str, str] | None = None,
) -> dict[str, Any] | None:
    """Return a randomly selected entry approach for the location.

    최근에 같은 장소에서 뽑힌 도입은 제외하고 선택한다.
    """
    approaches = location.get("entry_approaches") or []
    if not approaches:
        return None

    location_id = location.get("id", "")
    recent = None
    if recent_approaches is not None:
        recent = recent_approaches.get(location_id)

    # 최근에 뽑힌 건 제외하고 선택
    candidates = [a for a in approaches if a.get("id") != recent]
    if not candidates:
        candidates = approaches

    selected = dict(rng.choice(candidates))

    if recent_approaches is not None:
        recent_approaches[location_id] = selected.get("id", "")

    return selected


def select_scene(
    ep: int,
    char: Character,
    rng: random.Random | None = None,
    recent_approaches: dict[str, str] | None = None,
) -> dict[str, Any]:
    chooser = rng or random.Random()
    config = get_common_scene_config()
    names = character_names()
    character_index = names.index(char.name) if char.name in names else 0
    weights = config["scene_type_weights"]
    scene_types = ["work", "indoor"]
    scene_type = chooser.choices(
        scene_types,
        weights=[weights[name] for name in scene_types],
        k=1,
    )[0]
    location = chooser.choice(config["locations"][scene_type])
    outfit_pool = outfit_pool_for(char, config["outfits"])
    arcs = config["arcs"]
    arc = (
        pick(arcs, ep, character_index + 7)
        if arcs
        else location_driven_arc(char, location["place"])
    )
    arousal_elements = select_arousal_elements(location)
    entry_approach = select_entry_approach(location, chooser, recent_approaches)

    return {
        # 선택된 work/indoor location의 값을 빠뜨리지 않고 scene으로 전달한다.
        **location,
        "scene_type": scene_type,
        "weather": chooser.choice(location["weather_pool"]),
        "clothes": chooser.choice(outfit_pool[scene_type]),
        "hair": "캐릭터 프로필에 명시된 고유 헤어스타일을 유지한다",
        "arc_type": arc["type"],
        "start": arc["start"],
        "turn": arc["turn"],
        "after": arc["after"],
        "profile_name": char.name,
        "event_id": location["id"],
        "event_set_id": location["id"],
        "arousal_elements": arousal_elements,
        "entry_approach": entry_approach,
    }


def load_characters() -> list[Character]:
    characters: list[Character] = []
    for path in character_profile_paths():
        name = unicodedata.normalize("NFC", path.stem)
        profile = path.read_text(encoding="utf-8").strip()
        body_type = bullet_value(profile, "체형")
        if not body_type:
            raise ValueError(f"character body type not found: {name}")
        characters.append(
            Character(
                name=name,
                profile=profile,
                position=bullet_value(profile, "리부트 포지션"),
                body_type=body_type,
                speech=first_sentence(section(profile, "말투")),
                personality=first_sentence(section(profile, "성격")),
                appearance=first_sentence(section(profile, "외형")),
                points=section(profile, "장면 활용 포인트").replace("\n", " "),
                image_links=character_image_links(path),
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
        description="Generate outline files using character text profiles."
    )
    parser.add_argument("count", type=positive_count, help="Number of outlines to generate.")
    parser.add_argument("--character", help="Use one text-profiled character only.")
    return parser.parse_args(argv)


def selectable_characters(
    characters: list[Character],
    character_name: str | None = None,
) -> list[Character]:
    if character_name is None:
        if not characters:
            raise ValueError("no character text profiles found")
        return characters

    selected = [character for character in characters if character.name == character_name]
    if not selected:
        raise ValueError(f"character text profile not found: {character_name}")
    return selected


def arousal_elements_text(elements: list[dict[str, Any]]) -> str:
    if not elements:
        return ""
    lines = ["\n긴장 요소:"]
    for element in elements:
        trigger = element.get("trigger", "")
        timing = element.get("timing", "")
        effect = element.get("effect", "")
        line = f"- {trigger} — {timing}."
        if effect:
            line += f" {effect}."
        lines.append(line)
    return "\n".join(lines)


def entry_approach_text(approach: dict[str, Any] | None) -> str:
    if not approach:
        return ""
    lines = [
        "\n도입 접근 방식:",
        f"- 유형: {approach.get('type', '')}",
        f"- 시작 트리거: {approach.get('trigger', '')}",
        "- 단계별 전개:",
    ]
    for index, step in enumerate(approach.get("steps", []), start=1):
        lines.append(f"  {index}. {step}")
    return "\n".join(lines)


def outline_text(ep: int, char: Character, scene: dict[str, Any]) -> str:
    title = f"[{ep}화 성인씬 개요]"
    speech = char.speech or "가까워질수록 말투의 온도가 달라진다."
    personality = char.personality or "상대의 반응을 세심하게 살핀다."
    appearance = char.appearance or f"{char.name}은 장면 안에서 선명한 인상을 남기는 인물이다."
    points = char.points or char.position

    name_topic = f"{char.name}{subject_particle(char.name)}"
    name_nom = f"{char.name}{nominative_particle(char.name)}"
    visual_clothes = as_visual_sentence(scene["clothes"], " 차림이다.")
    visual_hair = as_visual_sentence(scene["hair"], " 상태다.")
    place_details = scene.get("place_details") or []
    place_detail_line = (
        f"- 장소 디테일: {', '.join(place_details)}.\n" if place_details else ""
    )
    arousal_elements = arousal_elements_text(scene.get("arousal_elements") or [])
    entry_approach = entry_approach_text(scene.get("entry_approach"))
    appearance_links = ", ".join(char.image_links) if char.image_links else "프로필 외형 설명 참고"

    return f"""{title}

이미지 프롬프트:
외형 참조: {appearance_links}
실사 스마트폰 사진 느낌의 고해상도 세로 인물 사진. 화면에는 성인 여성 {char.name} 한 명만 단독으로 등장한다. 얼굴, 눈매, 헤어스타일, 전체 분위기는 외형 참조 이미지를 기준으로 유지한다. {appearance} 헤어 스타일은 {visual_hair}. 2026년 여름, {scene['place']}에서 촬영된 장면이며 {visual_clothes} 차림이다. 장소의 공기감은 {scene['weather']}이다. 9:16 세로 구도, 얼굴과 상반신 중심의 인물 사진으로, 살짝 아래에서 올려다보거나 비스듬한 3/4 각도에서 목선과 쇄골, 상체 라인이 자연스럽게 드러난다. 과한 영화 조명이나 화보식 포즈 없이 실제 순간을 포착한 듯한 분위기 속에서, 담담하면서도 나른하고 은근한 관능미가 느껴지는 눈빛과 살짝 촉촉한 입술을 표현한다. 옷깃이나 헤어 사이로 쇄골과 어깨선이 살짝 드러난다. 현장 조명과 주변광이 섞인 자연스러운 빛, 현실적인 피부 질감과 머리카락, 옷감 디테일, 약간의 스마트폰 사진 노이즈와 자연스러운 색감을 유지한다. 배경은 살짝 흐릿하지만 {scene['place']}의 공간감이 자연스럽게 드러난다. 남성이나 다른 사람은 등장하지 않는다. no male, no other people, no crowd, no illustration, no anime, no CGI.



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
{arousal_elements}

이번 씬 복장:
- {name_topic} {scene['clothes']}.
- 헤어는 {scene['hair']}.
- 캐릭터 고유 분위기는 `{points}`의 소품과 동선을 일부 끌어와 살린다.
- 용식은 여름용 셔츠나 얇은 재킷 차림으로, 비나 열기 때문에 평소보다 느슨한 인상을 준다.

관계 구도:
- {name_topic} {personality}
- 말투는 {speech}
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
{entry_approach}
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
    rng: random.Random | None = None,
) -> list[Path]:
    chooser = rng or random.Random()
    characters = selectable_characters(load_characters(), character_name)
    config = get_common_scene_config()
    for char in characters:
        outfit_pool_for(char, config["outfits"])
    output_dir.mkdir(parents=True, exist_ok=True)
    written: list[Path] = []

    shuffled_pool: list[Character] = []
    recent_approaches: dict[str, str] = {}

    for ep in range(1, count + 1):
        # 특정 캐릭터 지정(--character)이 아닐 때만 셔플 루프 적용
        if character_name is None:
            if not shuffled_pool:
                shuffled_pool = characters.copy()
                chooser.shuffle(shuffled_pool)  # 무작위 셔플
            char = shuffled_pool.pop(0)
        else:
            char = characters[0]

        scene = select_scene(ep, char, chooser, recent_approaches)
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
