"""Character-specific outline generation profiles."""

from __future__ import annotations

import json
from pathlib import Path


JSON_PROFILE_DIR = Path(__file__).resolve().parent
COMMON_ARCS_PATH = JSON_PROFILE_DIR / "common_arcs.json"
COMMON_ARC_FIELDS = ("type", "start", "turn", "after")


def get_common_arcs() -> list[dict[str, str]]:
    try:
        payload = json.loads(COMMON_ARCS_PATH.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise ValueError(f"failed to load common arcs: {exc}") from exc

    arcs = payload.get("arcs") if isinstance(payload, dict) else None
    if not isinstance(arcs, list) or not arcs:
        raise ValueError("common arcs must be a non-empty list")

    required_fields = set(COMMON_ARC_FIELDS)
    for index, arc in enumerate(arcs):
        if not isinstance(arc, dict) or set(arc) != required_fields:
            raise ValueError(f"common arcs entry {index} has invalid fields")
        if any(
            not isinstance(arc[key], str) or not arc[key].strip()
            for key in COMMON_ARC_FIELDS
        ):
            raise ValueError(f"common arcs entry {index} has blank fields")

    return arcs


def get_profile(name: str) -> dict | None:
    json_path = JSON_PROFILE_DIR / f"{name}.json"
    if json_path.exists():
        return json.loads(json_path.read_text(encoding="utf-8"))

    return None
