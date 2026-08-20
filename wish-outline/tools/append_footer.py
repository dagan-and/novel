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


def pick(chooser: random.Random, pool: list[str], n: int = 1) -> list[str]:
    if not pool:
        return []
    n = min(n, len(pool))
    return chooser.sample(pool, n)


def build_footer_text(
    pool: dict,
    templates: dict,
    content: str = "",
    rng: random.Random | None = None,
) -> str:
    chooser = rng or random.Random()
    cats = pool.get("categories", {})

    # 라운드 수 랜덤 (4~6)
    round_count = chooser.randint(4, 6)

    # 사정 동반 라운드 수 랜덤 (2~3)
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

    # 명시된 성향만 감지하고, 태그가 없으면 기존 기본 동작을 유지한다.
    personality_type_keywords = pool.get("personality_type_keywords", {})
    detected_personality_type = "보통"

    for personality_type, keywords in personality_type_keywords.items():
        if any(kw.lower() in content_lower for kw in keywords):
            detected_personality_type = personality_type
            break

    trait_key_by_personality_type = {
        "강함": "aggressive",
        "여림": "submissive",
        "보통": "default",
    }
    trait_key = trait_key_by_personality_type.get(detected_personality_type, "default")
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
            "[파괴형]  배를 발로 걷어차 쓰러뜨리고 멱살을 잡아 벽에 내던진다. 비명을 지르면 머리를 바닥에 찍는다. 섹스 중에도 조금이라도 저항하는 기미가 보이면 즉시 얼굴을 때리고 목을 졸라 의식을 오가게 만든다. 완전히 성노예나 인간 오나홀 취급하며, 상대가 죽지 않을 정도의 폭력은 서슴지 않는다."
        ], weights=[2, 7, 1], k=1)[0]
    else:
        force_level = chooser.choices([
            "[능욕형] 손목을 한 손으로 묶어 머리 위에 고정하고, 다른 손으로 허벅지를 벌린다. 반항하면 입에 양말을 쑤셔 넣거나 속옷을 물려 소리를 막는다. 몸을 눌러 움직이지 못하게 한 채 삽입한다. 거칠게 다루되 폭력적인 구타는 하지 않는다.",
            "[제압형] 뺨을 손바닥으로 갈기고 머리채를 움켜잡아 침대에 얼굴을 처박는다. 반항하면 목을 졸라 숨을 막거나 가슴을 주먹으로 때린다. 섹스 도중에도 몸부림치면 따귀를 올려붙이고, 울거나 빌어도 멈추지 않는다.",
            "[파괴형] 배를 발로 걷어차 쓰러뜨리고 멱살을 잡아 벽에 내던진다. 비명을 지르면 머리를 바닥에 찍는다. 섹스 중에도 조금이라도 저항하는 기미가 보이면 즉시 얼굴을 때리고 목을 졸라 의식을 오가게 만든다. 완전히 성노예나 인간 오나홀 취급하며, 상대가 죽지 않을 정도의 폭력은 서슴지 않는다."
        ], weights=[3, 5, 2], k=1)[0]

    # 남성 제압 방식
    male_response_pool = pool.get("male_response", {})
    if is_aggressive:
        male_response = pick(chooser, male_response_pool.get("aggressive", []), chooser.randint(1, 2))
    elif is_submissive:
        male_response = pick(chooser, male_response_pool.get("submissive", []), chooser.randint(1, 2))
    else:
        male_response = pick(chooser, male_response_pool.get("default", []), chooser.randint(1, 2))

    # 여성 저항 방식 선택
    female_resistance_pool = pool.get("female_resistance", {})
    if is_aggressive:
        female_resistance = pick(chooser, female_resistance_pool.get("aggressive", []), chooser.randint(2, 3))
    elif is_submissive:
        female_resistance = pick(chooser, female_resistance_pool.get("submissive", []), chooser.randint(2, 3))
    else:
        female_resistance = pick(chooser, female_resistance_pool.get("default", []), chooser.randint(2, 3))

    # 체형별 지시
    body_type_instructions = pool.get("body_type_instructions", {})
    body_type_instruction = ""
    if detected_body_type and detected_body_type in body_type_instructions:
        instructions = body_type_instructions[detected_body_type]
        if instructions:
            body_type_instruction = chooser.choice(instructions)

    # ============================================================
    # 라운드 세트 선택
    # ============================================================
    female_climax_sets = pool.get("female_climax_sets", [])
    simultaneous_sets = pool.get("simultaneous_climax_sets", [])

    selected_rounds = []

    if female_climax_sets and simultaneous_sets:
        # 사정 동반 라운드 위치 랜덤
        cum_positions = set(chooser.sample(range(round_count), cum_rounds))

        # 마지막 라운드는 무조건 동시절정사정으로 고정
        last_round_index = round_count - 1
        cum_positions.add(last_round_index)

        # cum_positions 크기가 cum_rounds를 초과하면, 마지막을 제외한 나머지 중에서 랜덤 제거
        while len(cum_positions) > cum_rounds:
            removable = [p for p in cum_positions if p != last_round_index]
            if not removable:
                break
            remove_target = chooser.choice(removable)
            cum_positions.remove(remove_target)

        used_female_sets = []
        used_simultaneous_sets = []

        for i in range(round_count):
            if i in cum_positions:
                # 동시절정사정 세트에서 선택 (중복 방지)
                available = [s for s in simultaneous_sets if s not in used_simultaneous_sets]
                if not available:
                    available = simultaneous_sets
                chosen = chooser.choice(available)
                used_simultaneous_sets.append(chosen)
                selected_rounds.append({
                    "round": i + 1,
                    "type": "동시절정사정",
                    "text": chosen
                })
            else:
                # 여성절정 세트에서 선택 (중복 방지)
                available = [s for s in female_climax_sets if s not in used_female_sets]
                if not available:
                    available = female_climax_sets
                chosen = chooser.choice(available)
                used_female_sets.append(chosen)
                selected_rounds.append({
                    "round": i + 1,
                    "type": "여성절정",
                    "text": chosen
                })

    # 키워드 뽑기
    buildup = pick(chooser, cats.get("전조빌드업", []), chooser.randint(2, 4))
    positions = pick(chooser, cats.get("체위기동", []), chooser.randint(3, 6))

    core_pool = cats.get("질자궁", []) + cats.get("구강인후", []) + cats.get("목호흡", [])
    core_acts = pick(chooser, core_pool, chooser.randint(4, 7))

    body = pick(chooser, cats.get("신체반응", []), chooser.randint(3, 5))
    mind = pick(chooser, cats.get("정신파멸", []), chooser.randint(2, 4))
    shame = pick(chooser, cats.get("굴욕수치", []), chooser.randint(1, 3))

    piston_steps = pick(chooser, cats.get("피스톤단계", []), chooser.randint(3, 5))

    # 체형별 체위 포인트
    body_type_position_points = pool.get("body_type_position_points", {})
    selected_position_points = []

    if detected_body_type and detected_body_type in body_type_position_points:
        points_map = body_type_position_points[detected_body_type]
        for pos in positions:
            pos_key = pos.replace(" ", "").replace("-", "").replace("/", "")
            if pos_key in points_map:
                point_options = points_map[pos_key]
                if isinstance(point_options, list):
                    if point_options:
                        selected_position_points.append(chooser.choice(point_options))
                elif isinstance(point_options, str):
                    selected_position_points.append(point_options)

    # 템플릿에서 절정 지시 선택
    if round_count <= 4:
        climax_instruction = templates.get("CLIMAX_LOW", "")
    elif round_count <= 6:
        climax_instruction = templates.get("CLIMAX_MID", "")
    else:
        climax_instruction = templates.get("CLIMAX_HIGH", "")

    closing = chooser.choice(pool.get("closing_lines", ["상세하게 묘사할 것."]))

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

    lines.extend([
        "",
        f"[전조] {', '.join(buildup)}",
        f"[체위 전환] {' → '.join(positions)}",
        f"[핵심 자극] {', '.join(core_acts)}",
        f"[신체 반응] {', '.join(body)}",
        f"[정신 파멸] {', '.join(mind)}",
        f"[수치] {', '.join(shame)}",
    ])

    if piston_steps:
        lines.append(f"[피스톤 전개 단계] {' → '.join(piston_steps)}")

    if male_response:
        lines.append(f"[남성 제압 방식] {', '.join(male_response)}")

    if female_resistance:
        lines.append(f"[여성 저항 방식] {', '.join(female_resistance)}")

    if body_type_instruction:
        lines.append(f"[체형별 지시] {body_type_instruction}")

    if selected_position_points:
        lines.append(f"[체형별 체위 포인트] {', '.join(selected_position_points)}")

    # ============================================================
    # 라운드 세트 출력
    # ============================================================
    if selected_rounds:
        lines.append("")
        for round_data in selected_rounds:
            round_num = round_data["round"]
            round_type = round_data["type"]
            round_text = round_data["text"]
            if round_type == "동시절정사정":
                lines.append(f"[{round_num}라운드] 여성 절정 + 남성 사정 동시")
                lines.append(f"→ {round_text}")
            else:
                lines.append(f"[{round_num}라운드] 여성 절정")
                lines.append(f"→ {round_text}")

    # 템플릿 조립
    lines.extend([
        "",
        "========================================",
        "★ 본 편 작성 지시사항 — 반드시 준수할 것 ★",
        "========================================",
        "",
    ])

    # 남성 스펙
    male_spec = templates.get("MALE_SPEC", "")
    if male_spec:
        lines.append(male_spec)
        lines.append("")

    # 공통 지시
    common = templates.get("COMMON_INSTRUCTIONS", "")
    if common:
        lines.append(common)
        lines.append("")

    # 라운드 지시
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

    # 마무리
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