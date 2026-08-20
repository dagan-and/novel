"""Common configuration for outline generation."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any


JSON_PROFILE_DIR = Path(__file__).resolve().parent
COMMON_ARCS_PATH = JSON_PROFILE_DIR / "common_arcs.json"
COMMON_ARC_FIELDS = ("type", "start", "turn", "after")
SCENE_TYPES = ("work", "indoor")
BODY_TYPES = (
    "슬림글래머",
    "아담글래머",
    "늘씬한슬림",
    "균형잡힌비율",
    "가녀린슬렌더",
    "탄탄한스포티",
)
REQUIRED_LOCATION_FIELDS = {"id", "place", "weather_pool", "pressure", "place_details"}
AROUSAL_ELEMENT_FIELDS = {"trigger", "timing", "effect", "dialogue", "weight"}


def _load_common_payload() -> Any:
    try:
        return json.loads(COMMON_ARCS_PATH.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise ValueError(f"failed to load common scene config: {exc}") from exc


def _validated_string_pool(pool: Any, name: str) -> list[str]:
    if not isinstance(pool, list) or not pool or any(
        not isinstance(value, str) or not value.strip() for value in pool
    ):
        raise ValueError(f"{name} must be a non-empty list of non-blank strings")
    return pool


def get_common_scene_config() -> dict[str, Any]:
    payload = _load_common_payload()
    if not isinstance(payload, dict):
        raise ValueError("common scene config must be an object")
    if payload.get("scene_type_weights") != {"work": 60, "indoor": 40}:
        raise ValueError("scene_type_weights must be work=60 and indoor=40")

    locations = payload.get("locations")
    if not isinstance(locations, dict):
        raise ValueError("locations must be an object")
    for scene_type in SCENE_TYPES:
        entries = locations.get(scene_type)
        if not isinstance(entries, list) or not entries:
            raise ValueError(f"locations.{scene_type} must be a non-empty list")
        for index, entry in enumerate(entries):
            if not isinstance(entry, dict) or not REQUIRED_LOCATION_FIELDS.issubset(entry):
                raise ValueError(f"locations.{scene_type}[{index}] has invalid fields")
            for field in ("id", "place", "pressure"):
                value = entry[field]
                if not isinstance(value, str) or not value.strip():
                    raise ValueError(
                        f"locations.{scene_type}[{index}].{field} "
                        "must be a non-blank string"
                    )
            _validated_string_pool(
                entry["weather_pool"],
                f"locations.{scene_type}[{index}].weather_pool",
            )
            _validated_string_pool(
                entry["place_details"],
                f"locations.{scene_type}[{index}].place_details",
            )
            arousal_elements = entry.get("arousal_elements")
            if arousal_elements is not None:
                if not isinstance(arousal_elements, list):
                    raise ValueError(
                        f"locations.{scene_type}[{index}].arousal_elements must be a list"
                    )
                for element_index, element in enumerate(arousal_elements):
                    if not isinstance(element, dict) or not AROUSAL_ELEMENT_FIELDS.issubset(element):
                        raise ValueError(
                            f"locations.{scene_type}[{index}].arousal_elements"
                            f"[{element_index}] has invalid fields"
                        )
                    for field in ("trigger", "timing", "effect"):
                        value = element[field]
                        if not isinstance(value, str) or not value.strip():
                            raise ValueError(
                                f"locations.{scene_type}[{index}].arousal_elements"
                                f"[{element_index}].{field} must be a non-blank string"
                            )
                    weight = element["weight"]
                    if not isinstance(weight, (int, float)) or weight <= 0:
                        raise ValueError(
                            f"locations.{scene_type}[{index}].arousal_elements"
                            f"[{element_index}].weight must be a positive number"
                        )

    outfits = payload.get("outfits")
    if not isinstance(outfits, dict) or set(outfits) != set(BODY_TYPES):
        raise ValueError("outfits must contain every supported body type")
    for body_type in BODY_TYPES:
        pools = outfits[body_type]
        if not isinstance(pools, dict) or set(pools) != set(SCENE_TYPES):
            raise ValueError(f"outfits.{body_type} must contain work and indoor")
        for scene_type in SCENE_TYPES:
            _validated_string_pool(
                pools[scene_type],
                f"outfits.{body_type}.{scene_type}",
            )

    arcs = payload.get("arcs")
    if arcs is None or arcs == []:
        payload["arcs"] = []
    else:
        _validated_arcs(arcs)
    return payload


def get_common_arcs() -> list[dict[str, str]]:
    payload = _load_common_payload()
    if not isinstance(payload, dict):
        raise ValueError("common arcs must be a non-empty list")
    return _validated_arcs(payload.get("arcs"))


def _validated_arcs(arcs: Any) -> list[dict[str, str]]:
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
