#!/usr/bin/env python3
from __future__ import annotations

import argparse
import base64
import json
import os
import re
import sys
import urllib.error
import urllib.request
from pathlib import Path


ROOT = Path(__file__).resolve().parent
DEFAULT_TEMPLATE = ROOT / "images" / "gpt_lady_image.txt"
DEFAULT_CHAR_DIR = ROOT / "characters"
DEFAULT_OUTPUT_DIR = ROOT / "images" / "characters"
OPENAI_IMAGES_URL = "https://api.openai.com/v1/images/generations"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Build profile-image prompts from character markdown files and optionally generate images."
    )
    parser.add_argument(
        "targets",
        nargs="*",
        help="Character markdown files, stem names, or character names. Example: 오연서 or characters/오연서.md",
    )
    parser.add_argument(
        "--all",
        action="store_true",
        help="Process every markdown file under characters/ except templates and 김시안.md.",
    )
    parser.add_argument(
        "--template",
        default=str(DEFAULT_TEMPLATE),
        help="Prompt template text file.",
    )
    parser.add_argument(
        "--output-dir",
        default=str(DEFAULT_OUTPUT_DIR),
        help="Directory to save generated prompt files and images.",
    )
    parser.add_argument(
        "--model",
        default="gpt-image-2",
        help="OpenAI image model name.",
    )
    parser.add_argument(
        "--size",
        default="1024x1536",
        help="Output image size.",
    )
    parser.add_argument(
        "--quality",
        default="high",
        help="Output image quality.",
    )
    parser.add_argument(
        "--format",
        default="png",
        choices=["png", "jpeg", "webp"],
        help="Image file format.",
    )
    parser.add_argument(
        "--background",
        default="auto",
        help="Background option forwarded to the image API.",
    )
    parser.add_argument(
        "--prompt-only",
        action="store_true",
        help="Only write prompt files. Do not call the image API.",
    )
    parser.add_argument(
        "--force",
        action="store_true",
        help="Overwrite existing prompt/image files.",
    )
    return parser.parse_args()


def list_character_files() -> list[Path]:
    files = []
    for path in sorted(DEFAULT_CHAR_DIR.glob("*.md")):
        if path.name in {"김시안.md", "캐릭터양식.md"}:
            continue
        files.append(path)
    return files


def resolve_targets(targets: list[str], use_all: bool) -> list[Path]:
    if use_all:
        resolved = list_character_files()
        if not resolved:
            raise SystemExit("처리할 캐릭터 파일이 없습니다.")
        return resolved

    if not targets:
        raise SystemExit("대상 캐릭터를 지정하거나 --all 옵션을 사용해주세요.")

    candidates = {path.name: path for path in list_character_files()}
    candidates.update({path.stem: path for path in list_character_files()})

    resolved: list[Path] = []
    for raw in targets:
        path = Path(raw)
        if path.exists():
            resolved.append(path.resolve())
            continue

        matched = candidates.get(raw)
        if matched is None:
            matched = candidates.get(f"{raw}.md")
        if matched is None:
            raise SystemExit(f"대상 캐릭터를 찾을 수 없습니다: {raw}")
        resolved.append(matched.resolve())
    return resolved


def read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def extract_name(markdown: str, fallback: str) -> str:
    match = re.search(r"- 이름:\s*(.+)", markdown)
    return match.group(1).strip() if match else fallback


def extract_section(markdown: str, heading: str) -> str:
    pattern = rf"### {re.escape(heading)}\n\n(.*?)(?=\n-----|\n### |\n## |\Z)"
    match = re.search(pattern, markdown, re.S)
    return match.group(1).strip() if match else ""


def normalize_bullets(section_text: str) -> str:
    lines = []
    for raw_line in section_text.splitlines():
        line = raw_line.rstrip()
        if not line:
            continue
        if line.startswith("- "):
            lines.append(line)
        else:
            lines.append(f"- {line}")
    return "\n".join(lines)


def build_prompt(template_text: str, character_path: Path) -> str:
    markdown = read_text(character_path)
    name = extract_name(markdown, character_path.stem)
    fixed_profile = normalize_bullets(extract_section(markdown, "고정"))
    appearance = normalize_bullets(extract_section(markdown, "외형"))
    variable = normalize_bullets(extract_section(markdown, "[가변]"))

    prompt_parts = [
        template_text.strip(),
        "",
        f"[캐릭터 이름]\n{name}",
        "",
        "[고정 설정]",
        fixed_profile or "- 정보 없음",
        "",
        "[외형 설정]",
        appearance or "- 정보 없음",
        "",
        "[현재 상태]",
        variable or "- 정보 없음",
    ]
    return "\n".join(prompt_parts).strip() + "\n"


def ensure_parent(path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)


def write_text(path: Path, content: str, force: bool) -> None:
    if path.exists() and not force:
        raise FileExistsError(f"이미 존재합니다: {path}")
    ensure_parent(path)
    path.write_text(content, encoding="utf-8")


def request_openai_image(
    api_key: str,
    prompt: str,
    model: str,
    size: str,
    quality: str,
    image_format: str,
    background: str,
) -> bytes:
    payload = {
        "model": model,
        "prompt": prompt,
        "size": size,
        "quality": quality,
        "output_format": image_format,
        "background": background,
    }
    body = json.dumps(payload).encode("utf-8")
    request = urllib.request.Request(
        OPENAI_IMAGES_URL,
        data=body,
        headers={
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        },
        method="POST",
    )

    try:
        with urllib.request.urlopen(request) as response:
            data = json.loads(response.read().decode("utf-8"))
    except urllib.error.HTTPError as error:
        detail = error.read().decode("utf-8", errors="replace")
        raise RuntimeError(f"이미지 생성 요청 실패: {error.code} {detail}") from error
    except urllib.error.URLError as error:
        raise RuntimeError(f"이미지 생성 요청 실패: {error}") from error

    try:
        image_base64 = data["data"][0]["b64_json"]
    except (KeyError, IndexError, TypeError) as error:
        raise RuntimeError(f"예상하지 못한 응답 형식입니다: {data}") from error
    return base64.b64decode(image_base64)


def write_bytes(path: Path, content: bytes, force: bool) -> None:
    if path.exists() and not force:
        raise FileExistsError(f"이미 존재합니다: {path}")
    ensure_parent(path)
    path.write_bytes(content)


def safe_slug(name: str) -> str:
    return re.sub(r"[^\w가-힣.-]+", "_", name).strip("_") or "character"


def main() -> int:
    args = parse_args()
    template_path = Path(args.template).resolve()
    output_dir = Path(args.output_dir).resolve()
    character_paths = resolve_targets(args.targets, args.all)
    template_text = read_text(template_path)
    api_key = os.environ.get("OPENAI_API_KEY", "").strip()

    if not args.prompt_only and not api_key:
        raise SystemExit("OPENAI_API_KEY가 없어서 이미지 생성은 할 수 없습니다. --prompt-only로 프롬프트만 저장할 수 있습니다.")

    for character_path in character_paths:
        markdown = read_text(character_path)
        name = extract_name(markdown, character_path.stem)
        slug = safe_slug(character_path.stem)
        prompt = build_prompt(template_text, character_path)

        prompt_path = output_dir / f"{slug}.prompt.txt"
        image_path = output_dir / f"{slug}.{args.format}"

        write_text(prompt_path, prompt, args.force)
        print(f"[prompt] {name} -> {prompt_path}")

        if args.prompt_only:
            continue

        image_bytes = request_openai_image(
            api_key=api_key,
            prompt=prompt,
            model=args.model,
            size=args.size,
            quality=args.quality,
            image_format=args.format,
            background=args.background,
        )
        write_bytes(image_path, image_bytes, args.force)
        print(f"[image]  {name} -> {image_path}")

    return 0


if __name__ == "__main__":
    sys.exit(main())
