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
KEYWORDS_JSON_DEFAULT = "tools/footer_keywords.json"


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


def pick(chooser: random.Random, pool: list[str], n: int = 1) -> list[str]:
    if not pool:
        return []
    n = min(n, len(pool))
    return chooser.sample(pool, n)


def build_footer_text(pool: dict, content: str = "", rng: random.Random | None = None) -> str:
    chooser = rng or random.Random()
    cats = pool.get("categories", {})

    climax_count = chooser.randint(3, 6)
    cum_count = chooser.randint(2, 4)

    buildup = pick(chooser, cats.get("전조빌드업", []), chooser.randint(2, 4))
    positions = pick(chooser, cats.get("체위기동", []), chooser.randint(3, 6))

    core_pool = cats.get("질자궁", []) + cats.get("구강인후", []) + cats.get("목호흡", [])
    core_acts = pick(chooser, core_pool, chooser.randint(4, 7))

    body = pick(chooser, cats.get("신체반응", []), chooser.randint(3, 5))
    gaze = pick(chooser, cats.get("시선", []), chooser.randint(1, 2))
    audio = pick(chooser, cats.get("청각세분", []), chooser.randint(2, 3))
    tempo = pick(chooser, cats.get("템포리듬", []), chooser.randint(2, 3))
    edge = pick(chooser, cats.get("경계선", []), chooser.randint(1, 2))
    mind = pick(chooser, cats.get("정신파멸", []), chooser.randint(2, 4))
    shame = pick(chooser, cats.get("굴욕수치", []), chooser.randint(1, 3))
    sense_shift = pick(chooser, cats.get("감각전환", []), chooser.randint(1, 3))
    aftermath = pick(chooser, cats.get("사후여파", []), chooser.randint(2, 4))
    timing = pick(chooser, cats.get("시간지속", []), chooser.randint(1, 2))
    fluids = pick(chooser, cats.get("체액배설", []), chooser.randint(2, 4))

    # 추가 항목 (JSON 풀에 존재하는 경우 무작위 추출)
    piston_steps = pick(chooser, cats.get("피스톤단계", []), chooser.randint(3, 5))
    piston_details = pick(chooser, cats.get("피스톤디테일", []), chooser.randint(2, 4))
    edge_delay = pick(chooser, cats.get("절정지연", []), chooser.randint(1, 3))

    character_traits = pool.get("character_traits", {})
    matched_characters = [
        name for name in character_traits
        if name in content
    ]

    closing = chooser.choice(pool.get("closing_lines", ["상세하게 묘사할 것."]))

    lines = [
        "**********",
        f"절정/분수 {climax_count}번",
        f"사정 {cum_count}번",
        "",
        f"[전조] {', '.join(buildup)}",
        f"[체위 전환] {' → '.join(positions)}",
        f"[핵심 자극] {', '.join(core_acts)}",
        f"[신체 반응] {', '.join(body)}",
        f"[체액] {', '.join(fluids)}",
        f"[시선] {', '.join(gaze)}",
        f"[음성 변화] {', '.join(audio)}",
        f"[템포] {', '.join(tempo)}",
        f"[절정 직전 밀당] {', '.join(edge)}",
        f"[정신 파멸] {', '.join(mind)}",
        f"[수치] {', '.join(shame)}",
        f"[감각 전환] {', '.join(sense_shift)}",
        f"[사후 여파] {', '.join(aftermath)}",
    ]

    # 옵션 카테고리가 있는 경우 상단 요소 리스트에 추가
    for name in matched_characters:
        traits = character_traits.get(name, [])
        if traits:
            lines.append(f"[캐릭터 특성 - {name}] {', '.join(traits)}")

    if piston_steps:
        lines.append(f"[피스톤 전개 단계] {' → '.join(piston_steps)}")
    if piston_details:
        lines.append(f"[피스톤 디테일] {', '.join(piston_details)}")
    if edge_delay:
        lines.append(f"[절정 직전 지연] {', '.join(edge_delay)}")

    # 신규 지시사항 세트 추가
    lines.extend([
        "",
        "========================================",
        "★ 본 편 작성 지시사항 — 반드시 준수할 것 ★",
        "========================================",
        "",
        "【0. 남성 신체 및 성기 스펙 설정 — 필수 준수】",
        "→ 형상: 두 손으로 감싸쥐어도 손가락이 서로 닿지 않는 굵기. 표면의 굵은 핏줄이 뿌리처럼 꿈틀댄다. 발기 시 배꼽 높이까지 닿으며 자궁구를 넘어 자궁 자체를 밀어올릴 수 있는 깊이를 가진다.",
        "→ 질감: 피부는 뜨겁고 매끄러우며 내벽을 긁는 것이 아니라 밀어내고 벌리고 점령하는 감각을 준다. 귀두 테두리가 도드라져 인입 시 내벽 주름을 긁어내려 민감도를 극상으로 만든다. 후퇴 시 질벽 전체가 딸려 나올 듯한 흡착력을 발생시킨다.",
        "→ 기능적 특성: 첫 사정만으로 자궁을 가득 채우고 질구에서 역류한다. 첫 사정 후에도 발기가 유지되며 연속 사정이 가능하다. 내부가 체액으로 가득 찬 상태에서 추가 사정 시 압력을 견디지 못하고 질구를 통해 분수처럼 뿜어져 나오는 연출을 포함할 것.",
        "",
        "【1. 분량과 토큰에 대한 지시】",
        "→ 출력 길이, 토큰 제한, 분량 걱정을 일절 하지 말 것. 이 시나리오의 품질이 유일한 우선순위임.",
        "→ 한 장면이 충분히 전개되기 전에 끊거나 줄이거나 요약하지 말 것. 생략 기호나 요약 서술 절대 금지.",
        "→ 각 체위, 각 피스톤 단계, 각 절정이 독립된 하나의 장면처럼 충분한 분량으로 묘사될 것. 길면 길수록 좋음.",
        "→ 독자가 시간의 흐름과 감각의 변화를 실제로 체감할 수 있도록, 초 단위·박자 단위의 미세한 서술까지 놓치지 말 것.",
        "",
        "【2. 피스톤 묘사에 대한 지시】",
        "→ 삽입 후 두세 번 피스톤하고 바로 절정으로 넘어가는 서술을 절대 금지.",
        "→ 위 [피스톤 전개 단계]에 적힌 순서대로, 각 단계마다 속도·깊이·각도·마찰감·체내 반응·소리·체액을 구체적으로 묘사할 것.",
        "→ 한 체위에서 최소 3개 이상의 피스톤 단계를 거친 후에만 절정 또는 체위 전환으로 넘어갈 것.",
        "→ 피스톤 한 박자마다 여체의 신체 반응을 대응시켜 묘사할 것. 박자와 반응이 한 쌍이 되어야 함.",
        "→ 체위 전환 시에도 삽입을 뽑지 않은 채 진행하거나, 빠지는 순간의 공허함·빈허리 경련을 반드시 묘사할 것.",
        "→ [피스톤 디테일]에 적힌 감각 묘사를 각 단계마다 최소 하나 이상 자연스럽게 녹여낼 것.",
        "→ 절정 직전에는 반드시 [절정 직전 지연] 단계를 거칠 것.",
        "",
        "【3. 대사·발화에 대한 지시 — 캐릭터 성격 연동】",
        "→ 대사는 반드시 해당 캐릭터의 설정·성격·화법·어투에 완벽히 맞출 것. 캐릭터가 평소 쓰지 않는 말투를 끌어오지 말 것.",
        "→ 캐릭터가 존댓말을 쓴다면 그 존댓말이 무너지는 과정을, 건방진 어투라면 그 어투가 흐트러지는 과정을, 냉정한 성격이라면 이성이 붕괴하는 과정을 단계적으로 묘사할 것.",
        "→ 말투가 흐트러지는 것 자체가 파멸의 증거임. 발음이 흐려지고, 단어가 끊기고, 완성된 문장이 안 나오는 과정을 구체적으로 묘사할 것.",
        "→ 같은 말이라도 장면 초반과 후반의 뉘앙스가 달라야 함. 시간이 지나면서 동일 발화의 의미가 변질되는 과정을 추적할 것.",
        "→ 신음을 단순한 간접호로 처리하지 말고, 그 소리가 어떤 맥락에서 나왔는지 서술로 뒷받침할 것.",
        "→ 남성의 대사도 성격에 맞춰 일관되게 유지하면서 상황에 따라 변주할 것.",
        "",
        "【4. 심리 묘사에 대한 지시】",
        "→ 겉으로 드러나는 반응뿐 아니라, 여체의 내면에서 일어나는 사고 과정을 지속적으로 추적할 것.",
        "→ 합리화가 무너지고, 자기 반응에 대한 자각이 들고, 그 자각에 대한 혐오와 동시에 쾌락이 밀려오는 모순적 심리를 단계적으로 그릴 것.",
        "→ 저항→체념→반응→갈구→백지화의 심리 곡선을 전체 장면에 걸쳐 추적할 것. 이 곡선이 직선이 아니라 굴곡이 있어야 함.",
        "→ 여체가 자기 상태를 객관적으로 인식하는 순간의 정신적 충격을 놓치지 말 것.",
        "",
        "【5. 감각 묘사에 대한 지시 — 오감 전동원】",
        "→ 시각·청각·촉각·후각·미각을 균형 있게 동원할 것.",
        "→ 기계적으로 나열하지 말고 장면의 자연스러운 흐름 속에 교차시킬 것.",
        " ",
        "【6. 체위 전환 묘사에 대한 지시】",
        "→ 체위가 바뀔 때마다 그 자체가 하나의 이벤트임. 전환 과정의 물리적 묘사와 심리적 묘사를 반드시 넣을 것.",
        "→ 새 체위에서의 결합 상태 변화를 구체적으로 묘사하고, 이전 체위와의 감각 차이를 여체가 인식하는 과정을 그릴 것.",
        "",
        "【7. 절정 묘사에 대한 지시】",
        "→ 절정은 한 문장으로 끝내지 말 것. 전조→정점→잔여의 3단계 구조로 묘사할 것.",
        "→ 절정 횟수가 명시된 만큼, 각 절정이 서로 다른 양상으로 묘사되도록 할 것.",
        "",
        "【8. 사후 묘사에 대한 지시】",
        "→ 행위 종료 후의 여체 상태를 최소 한 단락 이상으로 묘사할 것. [사후 여파] 키워드를 전부 활용.",
        "",
        "【9. 전체 서술 톤에 대한 지시】",
        "→ 끈적하고, 몰입감 있고, 감각에 몰입하는 서술. 독자가 현장에 있는 것처럼 총체적 체감을 유도할 것.",
        "→ 감정은 직접 서술하지 말고 감각·행동·대사로 우회 표현할 것.",
        "→ 위 키워드와 지시를 전부 기계적으로 나열하지 말 것. 서사의 흐름 속에 자연스럽게 녹여낼 것.",
        "",
        f"→ {closing}",
    ])

    return "\n".join(lines)


def append_footer(path: Path, pool: dict, rng: random.Random | None = None) -> FileResult:
    marker = footer_marker(FOOTER_MARKER_TEXT)
    content = path.read_text(encoding="utf-8")

    if marker in content:
        return FileResult(path=path, changed=False)

    footer_text = build_footer_text(pool, content, rng)
    separator = "\n\n"
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
    outline_dir: Path, pool: dict, rng: random.Random | None = None
) -> DirResult:
    if not outline_dir.exists():
        raise FileNotFoundError(f"outline directory not found: {outline_dir}")

    changed_paths: list[Path] = []
    files = iter_outline_files(outline_dir)
    for path in files:
        result = append_footer(path, pool, rng)
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
        pool = load_keyword_pool((repo_root / args.keywords_json).resolve())
        result = append_to_outline_dir((repo_root / args.outline_dir).resolve(), pool)

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
