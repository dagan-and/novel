#!/usr/bin/env python3
"""outlines 생성, 푸터 추가, Git 푸시까지 한 번에 실행하는 원클릭 스크립트"""

import argparse
import sys
from pathlib import Path
from typing import Optional

# tools 폴더의 모듈들을 불러오기 위해 경로 추가
REPO_ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(REPO_ROOT / "tools"))

# 실제 파일명에 맞춰 import
import append_footer  # tools/append_footer.py
import generate_outlines  # generate_outlines.py
import push_outlines  # tools/push_outlines.py


def run_pipeline(
    count: int,
    character: Optional[str] = None,
    commit_msg: str = "Update outline files",
):
    print(f"=== 1. 개요 파일 {count}개 생성 시작 ===")
    written = generate_outlines.generate_outlines(
        count,
        character_name=character,
    )
    print(
        f"생성 완료: {len(written)}개 파일 "
        f"({written[0].name} ~ {written[-1].name})"
    )

    print("\n=== 2. 푸터(Footer) 추가 작업 시작 ===")
    keywords_path = REPO_ROOT / "tools" / "common_keywords.json"
    character_traits_path = REPO_ROOT / "tools" / "character_traits.json"
    templates_path = REPO_ROOT / "tools" / "common_templates.txt"
    outline_dir = REPO_ROOT / "outlines"

    pool = append_footer.load_footer_pool(keywords_path, character_traits_path)
    templates = append_footer.load_templates(templates_path)

    dir_result = append_footer.append_to_outline_dir(
        outline_dir,
        pool,
        templates,
    )

    print(
        f"스캔 완료: {dir_result.scanned_count}개 / "
        f"변경 완료: {dir_result.changed_count}개"
    )

    print("\n=== 3. Git Commit & Push 시작 ===")
    push_result = push_outlines.push_outlines(
        repo_root=REPO_ROOT,
        outline_dir="outlines",
        message=commit_msg,
    )

    if push_result.pushed:
        print(
            f"성공적으로 푸시되었습니다: "
            f"{push_result.remote}/{push_result.branch}"
        )
    else:
        print("푸시할 변경 사항이 없습니다.")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Generate, Append, and Push in one go.")
    parser.add_argument("count", type=generate_outlines.positive_count, help="생성할 개요 수")
    parser.add_argument("--character", help="특정 캐릭터 지정")
    parser.add_argument("--message", default="Update outline files", help="커밋 메시지")

    args = parser.parse_args()
    run_pipeline(args.count, args.character, args.message)
