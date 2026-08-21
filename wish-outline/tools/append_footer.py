#!/usr/bin/env python3
"""Append a one-time footer to outline files and optionally commit/push it."""

from __future__ import annotations

import argparse
import hashlib
import json
import random
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path


TEXT_EXTENSIONS = {".txt"}
FOOTER_MARKER_TEXT = "outline-random-footer-v1"
PROJECT_ROOT = Path(__file__).resolve().parents[1]
CHARACTER_JSON_DEFAULT = "tools/character_traits.json"
KEYWORDS_JSON_DEFAULT = "tools/common_keywords.json"
TEMPLATES_DEFAULT = "tools/common_templates.txt"


@dataclass(frozen=True)
class FileResult:
    path: Path
    changed: bool


@dataclass(frozen=True)
class DirResult:
    scanned_count: int
    changed_count: int
    changed_paths: tuple[Path, ...]


def footer_id(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()[:16]


def footer_marker(text: str) -> str:
    return f"<!-- outline-footer:{footer_id(text)} -->"


def load_keyword_pool(json_path: Path) -> dict:
    with json_path.open(encoding="utf-8") as f:
        return json.load(f)


def load_footer_pool(keywords_path: Path, character_path: Path) -> dict:
    pool = load_keyword_pool(keywords_path)
    character_pool = load_keyword_pool(character_path)
    return {**pool, **character_pool}


def load_templates(path: Path) -> dict:
    templates = {}
    current_key = None
    current_lines = []

    with path.open(encoding="utf-8") as f:
        for line in f:
            line = line.rstrip("\n")
            if line.startswith("===") and line.endswith("==="):
                if current_key is not None:
                    templates[current_key] = "\n".join(current_lines).strip()
                current_key = line.strip("=")
                current_lines = []
            else:
                current_lines.append(line)
        if current_key is not None:
            templates[current_key] = "\n".join(current_lines).strip()

    return templates


def pick(chooser: random.Random, pool: list, n: int = 1) -> list:
    if not pool:
        return []
    n = min(n, len(pool))
    return chooser.sample(pool, n)


def item_at(items: list, index: int):
    if not items:
        return ""
    return items[index % len(items)]


def join_nonempty(items: list[str]) -> str:
    return ", ".join(item for item in items if item)


def round_result_label(round_type: str) -> str:
    if round_type == "동시절정사정":
        return "여성 절정 + 남성 사정 동시"
    if round_type == "첫질내사정":
        return "여성 절정 + 첫 질내 사정"
    if round_type == "중간질내사정":
        return "여성 절정 + 중간 질내 사정"
    if round_type == "굴욕사정":
        return "여성 절정 + 남성 굴욕 사정"
    return "여성 절정"


def get_trait_key(trait: str) -> str:
    trait_lower = trait.lower()
    if "강함" in trait_lower or "aggressive" in trait_lower or "dominant" in trait_lower:
        return "aggressive"
    if (
        "여림" in trait_lower
        or "순종" in trait_lower
        or "submissive" in trait_lower
        or "약함" in trait_lower
    ):
        return "submissive"
    return "default"


def trait_pool(pool: list | dict, trait_key: str) -> list:
    if isinstance(pool, dict):
        return pool.get(trait_key, pool.get("default", []))
    return pool


def pick_from_position_pool(
    positions: list[dict],
    round_count: int,
    chooser: random.Random,
) -> list[dict]:
    if not positions:
        return []

    selected = chooser.sample(positions, min(round_count, len(positions)))
    while len(selected) < round_count:
        remaining = [p for p in positions if p not in selected]
        if not remaining:
            remaining = positions
        selected.append(chooser.choice(remaining))
    return selected


def pick_unique_from_list(
    pool: list[str],
    used: list[str],
    chooser: random.Random,
) -> str:
    candidates = [item for item in pool if item not in used]
    if not candidates:
        candidates = pool
    if not candidates:
        return ""
    return chooser.choice(candidates)


def build_fallback_resistance_pairs(pool: dict, trait_key: str) -> list[dict]:
    resistance_pool = pool.get("female_resistance", {})
    response_pool = pool.get("male_response", {})
    resistances = resistance_pool.get(trait_key, resistance_pool.get("default", []))
    responses = response_pool.get(trait_key, response_pool.get("default", []))

    return [
        {"저항": resistance, "제압": response}
        for resistance, response in zip(resistances, responses)
    ]


def pick_resistance_pairs(
    pool: dict,
    trait_key: str,
    round_count: int,
    chooser: random.Random,
) -> list[dict]:
    pair_pool = pool.get("저항제압", {})
    trait_pairs = pair_pool.get(trait_key, pair_pool.get("default", []))
    if not trait_pairs:
        trait_pairs = build_fallback_resistance_pairs(pool, trait_key)
    if not trait_pairs:
        return []

    selected_pairs = chooser.sample(trait_pairs, min(len(trait_pairs), round_count))
    while len(selected_pairs) < round_count:
        remaining = [pair for pair in trait_pairs if pair not in selected_pairs]
        if not remaining:
            remaining = trait_pairs
        selected_pairs.append(chooser.choice(remaining))

    return selected_pairs


def build_position_pool_from_categories(cats: dict) -> list[dict]:
    positions = cats.get("체위기동", [])
    pistons = cats.get("피스톤단계", [])
    cores = cats.get("질자궁", []) + cats.get("구강인후", []) + cats.get("목호흡", [])
    bodies = cats.get("신체반응", [])

    if not any((positions, pistons, cores, bodies)):
        return []

    base_positions = positions or [""]
    return [
        {
            "name": position,
            "피스톤": pistons,
            "코어자극": cores,
            "신체반응": bodies,
        }
        for position in base_positions
    ]


def build_round_data(
    positions: list[dict],
    round_count: int,
    chooser: random.Random,
) -> list[dict]:
    selected_positions = pick_from_position_pool(positions, round_count, chooser)

    used_pistons: list[str] = []
    used_cores: list[str] = []
    used_bodies: list[str] = []

    round_data = []

    for pos in selected_positions:
        piston = pick_unique_from_list(pos.get("피스톤", []), used_pistons, chooser)
        used_pistons.append(piston)

        core = pick_unique_from_list(pos.get("코어자극", []), used_cores, chooser)
        used_cores.append(core)

        body = pick_unique_from_list(pos.get("신체반응", []), used_bodies, chooser)
        used_bodies.append(body)

        round_data.append({
            "position": pos["name"],
            "piston": piston,
            "core": core,
            "body": body,
        })

    while len(round_data) < round_count:
        round_data.append({
            "position": "",
            "piston": "",
            "core": "",
            "body": "",
        })

    return round_data


def build_footer_text(
    pool: dict,
    templates: dict,
    content: str = "",
    rng: random.Random | None = None,
) -> str:
    chooser = rng or random.Random()
    cats = pool.get("categories", {})

    round_count = chooser.randint(4, 6)
    cum_rounds = chooser.randint(2, 3)

    content_lower = content.lower()

    # 체형 감지
    body_type_keywords = pool.get("body_type_keywords", {})
    body_type_order = pool.get("body_type_order", list(body_type_keywords.keys()))
    detected_body_type = None

    for body_type in body_type_order:
        keywords = body_type_keywords.get(body_type, [])
        if any(kw.lower() in content_lower for kw in keywords):
            detected_body_type = body_type
            break

    # 성향 감지
    personality_type_keywords = pool.get("personality_type_keywords", {})
    detected_personality_type = "보통"

    for personality_type, keywords in personality_type_keywords.items():
        if any(kw.lower() in content_lower for kw in keywords):
            detected_personality_type = personality_type
            break

    trait_key = get_trait_key(detected_personality_type)
    is_aggressive = trait_key == "aggressive"
    is_submissive = trait_key == "submissive"

    # 강제성 수준
    if is_aggressive:
        force_level = chooser.choices([
            "[능욕형] 손목을 한 손으로 묶어 머리 위에 고정하고, 다른 손으로 허벅지를 벌린다. 반항하면 입에 양말을 쑤셔 넣거나 속옷을 물려 소리를 막는다. 몸을 눌러 움직이지 못하게 한 채 삽입한다. 거칠게 다루되 폭력적인 구타는 하지 않는다.",
            "[제압형] 뺨을 손바닥으로 갈기고 머리채를 움켜잡아 침대에 얼굴을 처박는다. 반항하면 목을 졸라 숨을 막거나 가슴을 주먹으로 때린다. 섹스 도중에도 몸부림치면 따귀를 올려붙이고, 울거나 빌어도 멈추지 않는다.",
            "[파괴형] 배를 발로 걷어차 쓰러뜨리고 멱살을 잡아 벽에 내던진다. 비명을 지르면 머리를 바닥에 찍는다. 섹스 중에도 조금이라도 저항하는 기미가 보이면 즉시 얼굴을 때리고 목을 졸라 의식을 오가게 만든다. 완전히 성노예나 인간 오나홀 취급하며, 상대가 죽지 않을 정도의 폭력은 서슴지 않는다."
        ], weights=[1, 4, 5], k=1)[0]
    elif is_submissive:
        force_level = chooser.choices([
            "[능욕형] 손목을 한 손으로 묶어 머리 위에 고정하고, 다른 손으로 허벅지를 벌린다. 반항하면 입에 양말을 쑤셔 넣거나 속옷을 물려 소리를 막는다. 몸을 눌러 움직이지 못하게 한 채 삽입한다. 거칠게 다루되 폭력적인 구타는 하지 않는다.",
            "[제압형] 뺨을 손바닥으로 갈기고 머리채를 움켜잡아 침대에 얼굴을 처박는다. 반항하면 목을 졸라 숨을 막거나 가슴을 주먹으로 때린다. 섹스 도중에도 몸부림치면 따귀를 올려붙이고, 울거나 빌어도 멈추지 않는다.",
            "[파괴형] 배를 발로 걷어차 쓰러뜨리고 멱살을 잡아 벽에 내던진다. 비명을 지르면 머리를 바닥에 찍는다. 섹스 중에도 조금이라도 저항하는 기미가 보이면 즉시 얼굴을 때리고 목을 졸라 의식을 오가게 만든다. 완전히 성노예나 인간 오나홀 취급하며, 상대가 죽지 않을 정도의 폭력은 서슴지 않는다."
        ], weights=[2, 7, 1], k=1)[0]
    else:
        force_level = chooser.choices([
            "[능욕형] 손목을 한 손으로 묶어 머리 위에 고정하고, 다른 손으로 허벅지를 벌린다. 반항하면 입에 양말을 쑤셔 넣거나 속옷을 물려 소리를 막는다. 몸을 눌러 움직이지 못하게 한 채 삽입한다. 거칠게 다루되 폭력적인 구타는 하지 않는다.",
            "[제압형] 뺨을 손바닥으로 갈기고 머리채를 움켜잡아 침대에 얼굴을 처박는다. 반항하면 목을 졸라 숨을 막거나 가슴을 주먹으로 때린다. 섹스 도중에도 몸부림치면 따귀를 올려붙이고, 울거나 빌어도 멈추지 않는다.",
            "[파괴형] 배를 발로 걷어차 쓰러뜨리고 멱살을 잡아 벽에 내던진다. 비명을 지르면 머리를 바닥에 찍는다. 섹스 중에도 조금이라도 저항하는 기미가 보이면 즉시 얼굴을 때리고 목을 졸라 의식을 오가게 만든다. 완전히 성노예나 인간 오나홀 취급하며, 상대가 죽지 않을 정도의 폭력은 서슴지 않는다."
        ], weights=[3, 5, 2], k=1)[0]

    selected_pairs = pick_resistance_pairs(pool, trait_key, round_count, chooser)
    resistance_rounds = set(range(0, round_count, 2))

    # 체형별 지시
    body_type_instructions = pool.get("body_type_instructions", {})
    body_type_instruction = ""
    if detected_body_type and detected_body_type in body_type_instructions:
        instructions = body_type_instructions[detected_body_type]
        if instructions:
            body_type_instruction = chooser.choice(instructions)

    # 체위별 풀에서 라운드 데이터 구성
    positions_pool = pool.get("체위", []) or build_position_pool_from_categories(cats)
    round_data = build_round_data(positions_pool, round_count, chooser)

    # 라운드 세트 선택 (절정/사정)
    female_climax_sets = pool.get("female_climax_sets", [])
    female_pool = trait_pool(female_climax_sets, trait_key)
    simultaneous_sets = pool.get("simultaneous_climax_sets", [])
    mid_cum_sets = pool.get("mid_cum_sets", []) or simultaneous_sets
    facial_cum_sets = pool.get("facial_cum_sets", []) or simultaneous_sets

    selected_rounds = []

    if female_pool and simultaneous_sets:
        last_round_index = round_count - 1
        other_positions = [i for i in range(round_count - 1)]
        internal_positions = sorted(
            chooser.sample(other_positions, min(max(0, cum_rounds - 1), len(other_positions)))
        )
        first_internal = internal_positions[0] if internal_positions else None
        mid_internal = (
            set(internal_positions[1:])
            if len(internal_positions) > 1
            else set()
        )

        used_female_sets = []
        used_simultaneous_sets = []
        used_mid_cum_sets = []
        used_facial_sets = []

        for i in range(round_count):
            if i == last_round_index:
                available = [s for s in facial_cum_sets if s not in used_facial_sets]
                if not available:
                    available = facial_cum_sets
                chosen = chooser.choice(available)
                used_facial_sets.append(chosen)
                selected_rounds.append({
                    "round": i + 1,
                    "type": "굴욕사정",
                    "text": chosen
                })
            elif i == first_internal:
                available = [s for s in simultaneous_sets if s not in used_simultaneous_sets]
                if not available:
                    available = simultaneous_sets
                chosen = chooser.choice(available)
                used_simultaneous_sets.append(chosen)
                selected_rounds.append({
                    "round": i + 1,
                    "type": "첫질내사정",
                    "text": chosen
                })
            elif i in mid_internal:
                available = [s for s in mid_cum_sets if s not in used_mid_cum_sets]
                if not available:
                    available = mid_cum_sets
                chosen = chooser.choice(available)
                used_mid_cum_sets.append(chosen)
                selected_rounds.append({
                    "round": i + 1,
                    "type": "중간질내사정",
                    "text": chosen
                })
            else:
                available = [s for s in female_pool if s not in used_female_sets]
                if not available:
                    available = female_pool
                chosen = chooser.choice(available)
                used_female_sets.append(chosen)
                selected_rounds.append({
                    "round": i + 1,
                    "type": "여성절정",
                    "text": chosen
                })

    # 기타 키워드
    buildup = pick(chooser, cats.get("전조빌드업", []), chooser.randint(2, 4))
    shame = pick(chooser, cats.get("굴욕수치", []), chooser.randint(1, 3))

    closing = chooser.choice(pool.get("closing_lines", ["상세하게 묘사할 것."]))

    # 출력 조립
    lines = [
        "**********",
        f"라운드 {round_count}번 (여성 절정 {round_count}회, 남성 사정 {cum_rounds}회)",
        f"강제성: {force_level}",
    ]

    if detected_body_type:
        body_type_outputs = pool.get("body_type_outputs", {})
        body_type_output = body_type_outputs.get(detected_body_type, detected_body_type)
        lines.append(f"체형: {body_type_output}")
    lines.append(f"성향: {detected_personality_type}")

    if body_type_instruction:
        lines.extend(["", f"[체형별 지시] {body_type_instruction}"])

    if selected_rounds:
        lines.extend(["", "[순차 진행표]"])
        late_round_note = templates.get("ROUND_NOTE_LATE", "").strip()
        last_round_note = templates.get("ROUND_NOTE_LAST", "").strip()

        for index, round_info in enumerate(selected_rounds):
            round_num = round_info["round"]
            rd = round_data[index]
            next_rd = round_data[index + 1] if index + 1 < len(round_data) else None

            position = rd["position"]
            next_position = next_rd["position"] if next_rd else None
            piston = rd["piston"]
            core = rd["core"]
            body_reaction = rd["body"]
            shame_point = item_at(shame, index)
            result = round_result_label(round_info["type"])

            lines.extend(["", f"[{round_num}구간: {position or '구도 지정'}]"])

            if round_num == 1 and buildup:
                lines.append(f"도입은 {join_nonempty(buildup)} 흐름으로 시작한다.")

            if position:
                if next_position and round_num < round_count:
                    lines.append(
                        f"이 구간은 {position} 구도로 진행하고, 다음 구간의 {next_position} 전환을 염두에 둔다."
                    )
                else:
                    lines.append(f"이 구간은 {position} 구도로 진행한다.")

            if piston or core:
                parts = []
                if piston:
                    parts.append(f"피스톤 전개는 {piston}을 중심으로 잡는다")
                if core:
                    parts.append(f"핵심 자극은 {core}를 배치한다")
                lines.append(" ".join(parts) + ".")

            if index in resistance_rounds and selected_pairs:
                response_parts = []
                pair = selected_pairs[index]
                resistance = pair.get("저항", "")
                response = pair.get("제압", "")
                if resistance:
                    response_parts.append(f"여성 저항은 {resistance}로 잡는다")
                if response:
                    response_parts.append(f"남성 제압 방식은 {response}를 사용한다")
                if response_parts:
                    lines.append(" ".join(response_parts) + ".")

            if body_reaction:
                lines.append(f"신체 반응은 {body_reaction}을 중심으로 묘사한다.")

            if shame_point and round_num == round_count:
                lines.append(f"수치 요소는 {shame_point}를 이 구간에 섞는다.")

            if round_num == 3 and late_round_note:
                lines.append(late_round_note)

            if round_num == round_count and last_round_note:
                lines.append(last_round_note)

            lines.append(f"결과: {result}.")
            if round_info["text"]:
                lines.append(f"세부 결과 메모: {round_info['text']}")

    # 템플릿 조립
    lines.extend([
        "",
        "========================================",
        "★ 본 편 작성 지시사항 — 반드시 준수할 것 ★",
        "========================================",
        "",
    ])

    male_spec = templates.get("MALE_SPEC", "")
    if male_spec:
        lines.append(male_spec)
        lines.append("")

    common = templates.get("COMMON_INSTRUCTIONS", "")
    if common:
        lines.append(common)
        lines.append("")

    if selected_rounds:
        lines.append("【7. 라운드 묘사에 대한 지시】")
        lines.append("→ 절정 횟수와 사정 횟수는 서술의 기준점일 뿐, 실제 서사에서는 절대로 구분하거나 표기하지 말 것.")
        lines.append("→ '1라운드', '2라운드' 같은 장면 구분, 소제목, 문단 나눔, 전환 표시를 절대 넣지 말 것.")
        lines.append("→ 여성 절정과 남성 사정은 피스톤의 연장선 위에서 자연스럽게 발생하며, 절정이 끝난 직후에도 피스톤이 멈추지 않고 다음 절정으로 이어질 것.")
        lines.append("→ 절정과 절정 사이의 간격은 체위 전환, 대화, 공간 묘사로 채우되, 서사가 끊기지 않도록 전환 과정 자체를 피스톤의 연장선으로 쓸 것.")
        lines.append("→ 체위 전환은 성기를 뽑는 순간의 공허감, 빼는 동안의 질벽 흡착, 재삽입 시의 각도 변화를 모두 서술해 전환이 곧 삽입의 연장이 되도록 할 것.")
        lines.append("→ 절정 직전에 피스톤을 멈추지 말 것. 절정이 밀려오면 오히려 더 강하게 몰아붙일 것.")
        lines.append("→ 절정 묘사 직후에는 반드시 다음 문장에서 피스톤이 이어지고 있어야 한다. 절정으로 문단이 끝나지 말 것. 절정 → 과민 반응 → 다음 체위 전환 or 다음 피스톤 단계가 한 호흡으로 연결되어야 한다.")
        lines.append("→ 비성적 대화나 공간 묘사는 피스톤이 계속되는 와중에 삽입할 것. 피스톤을 멈추고 대화하는 장면을 만들지 말 것.")
        lines.append("")

    lines.append(f"→ {closing}")

    return "\n".join(lines)


def append_footer(path: Path, pool: dict, templates: dict, rng: random.Random | None = None) -> FileResult:
    marker = footer_marker(FOOTER_MARKER_TEXT)
    content = path.read_text(encoding="utf-8")

    if marker in content:
        return FileResult(path=path, changed=False)

    footer_text = build_footer_text(pool, templates, content, rng)
    separator = "\n"
    updated = f"{content}{separator}{marker}\n{footer_text}\n"
    path.write_text(updated, encoding="utf-8")
    return FileResult(path=path, changed=True)


def iter_outline_files(outline_dir: Path) -> list[Path]:
    return sorted(
        path
        for path in outline_dir.rglob("*")
        if path.is_file() and path.suffix.lower() in TEXT_EXTENSIONS
    )


def append_to_outline_dir(
    outline_dir: Path,
    pool: dict,
    templates: dict,
    rng: random.Random | None = None,
) -> DirResult:
    if not outline_dir.exists():
        raise FileNotFoundError(f"outline directory not found: {outline_dir}")

    changed_paths: list[Path] = []
    files = iter_outline_files(outline_dir)
    for path in files:
        result = append_footer(path, pool, templates, rng)
        if result.changed:
            changed_paths.append(path)

    return DirResult(
        scanned_count=len(files),
        changed_count=len(changed_paths),
        changed_paths=tuple(changed_paths),
    )


def run_git(args: list[str], cwd: Path) -> None:
    subprocess.run(["git", *args], cwd=cwd, check=True)


def display_path(path: Path, repo_root: Path) -> str:
    try:
        return str(path.relative_to(repo_root))
    except ValueError:
        return str(path)


def commit_and_push(repo_root: Path, paths: tuple[Path, ...], message: str, push: bool) -> None:
    if not paths:
        print("No changed outline files to commit.")
        return

    relative_paths = [str(path.relative_to(repo_root)) for path in paths]
    run_git(["add", "--", *relative_paths], repo_root)
    run_git(["commit", "-m", message], repo_root)

    if push:
        branch = subprocess.check_output(
            ["git", "branch", "--show-current"],
            cwd=repo_root,
            text=True,
        ).strip()
        if not branch:
            raise RuntimeError("cannot push from detached HEAD")
        run_git(["push", "origin", branch], repo_root)


def parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Append the random footer block to every .txt file in outlines once."
    )
    parser.add_argument("--outline-dir", default="outlines")
    parser.add_argument(
        "--keywords-json",
        default=KEYWORDS_JSON_DEFAULT,
        help="Path to the JSON file holding the keyword pool.",
    )
    parser.add_argument(
        "--character-json",
        default=CHARACTER_JSON_DEFAULT,
        help="Path to the JSON file holding the keyword pool.",
    )
    parser.add_argument(
        "--templates",
        default=TEMPLATES_DEFAULT,
        help="Path to the text file holding instruction templates.",
    )
    parser.add_argument("--commit", action="store_true")
    parser.add_argument("--push", action="store_true")
    parser.add_argument(
        "--message",
        default="Update outline footer",
        help="Git commit message used with --commit.",
    )
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv or sys.argv[1:])
    repo_root = PROJECT_ROOT

    try:
        pool = load_footer_pool(
            (repo_root / args.keywords_json).resolve(),
            (repo_root / args.character_json).resolve(),
        )
        templates = load_templates((repo_root / args.templates).resolve())
        result = append_to_outline_dir((repo_root / args.outline_dir).resolve(), pool, templates)

        print(f"Scanned: {result.scanned_count}")
        print(f"Changed: {result.changed_count}")
        for path in result.changed_paths:
            print(display_path(path, repo_root))

        if args.push and not args.commit:
            raise ValueError("--push requires --commit")
        if args.commit:
            commit_and_push(repo_root, result.changed_paths, args.message, args.push)
    except Exception as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
