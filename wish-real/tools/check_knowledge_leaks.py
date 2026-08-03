#!/usr/bin/env python3
"""Check episode dialogue/message lines for forbidden character knowledge.

Usage:
    python3 tools/check_knowledge_leaks.py episodes/101-200/ep.153.md \
        --forbid '김초연:나고야' --forbid '김초연:유즈키'

The check is intentionally simple and strict: if a line starts with
[Character] and contains a forbidden term for that character, it fails.
Use it as a guardrail before HTML conversion and push.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path


SPEAKER_RE = re.compile(r"^\[(?P<speaker>[^\]]+)\]\s*(?P<body>.*)$")


def parse_forbid(values: list[str]) -> dict[str, list[str]]:
    rules: dict[str, list[str]] = {}
    for value in values:
        if ":" not in value:
            raise SystemExit(f"--forbid must be 'speaker:term', got: {value}")
        speaker, term = value.split(":", 1)
        speaker = speaker.strip()
        term = term.strip()
        if not speaker or not term:
            raise SystemExit(f"--forbid must be 'speaker:term', got: {value}")
        rules.setdefault(speaker, []).append(term)
    return rules


def scan_file(path: Path, rules: dict[str, list[str]]) -> list[str]:
    findings: list[str] = []
    try:
        text = path.read_text(encoding="utf-8")
    except UnicodeDecodeError:
        text = path.read_text()

    for lineno, line in enumerate(text.splitlines(), start=1):
        match = SPEAKER_RE.match(line)
        if not match:
            continue
        speaker = match.group("speaker").strip()
        body = match.group("body")
        for term in rules.get(speaker, []):
            if term in body:
                findings.append(f"{path}:{lineno}: [{speaker}] contains forbidden term '{term}': {body}")
    return findings


def load_rules_from_knowledge(path: Path) -> dict[str, list[str]]:
    data = json.loads(path.read_text(encoding="utf-8"))
    rules: dict[str, list[str]] = {}
    for entry in data.get("characters", {}).values():
        speaker = entry.get("display_name")
        terms = entry.get("forbidden_dialogue_terms", [])
        if not speaker or not isinstance(terms, list):
            continue
        clean_terms = [str(term).strip() for term in terms if str(term).strip()]
        if clean_terms:
            rules.setdefault(speaker, []).extend(clean_terms)
    return rules


def merge_rules(*rule_sets: dict[str, list[str]]) -> dict[str, list[str]]:
    merged: dict[str, list[str]] = {}
    for rules in rule_sets:
        for speaker, terms in rules.items():
            merged.setdefault(speaker, [])
            for term in terms:
                if term not in merged[speaker]:
                    merged[speaker].append(term)
    return merged


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("paths", nargs="+", type=Path)
    parser.add_argument("--forbid", action="append", default=[], help="Forbidden speaker knowledge as 'speaker:term'.")
    parser.add_argument(
        "--knowledge-state",
        type=Path,
        help="Load forbidden_dialogue_terms from states/knowledge_state.json.",
    )
    args = parser.parse_args()

    rules = parse_forbid(args.forbid)
    if args.knowledge_state:
        rules = merge_rules(load_rules_from_knowledge(args.knowledge_state), rules)
    if not rules:
        parser.error("At least one --forbid rule or --knowledge-state is required.")

    findings: list[str] = []
    for path in args.paths:
        findings.extend(scan_file(path, rules))

    if findings:
        print("Knowledge leak check failed:", file=sys.stderr)
        for finding in findings:
            print(finding, file=sys.stderr)
        return 1

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
