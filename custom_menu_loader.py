"""
Custom menu JSON loader and safe master update helpers.
"""

from __future__ import annotations

import glob
import json
import os
from collections import OrderedDict
from dataclasses import dataclass
from typing import Dict, List, Optional, Tuple

from config import MENU_ITEMS_DIR


@dataclass
class DishPointer:
    file_path: str
    cuisine_index: int
    dish_index: int


def _json_files() -> List[str]:
    pattern = os.path.join(MENU_ITEMS_DIR, "*.json")
    return sorted(
        p for p in glob.glob(pattern)
        if os.path.basename(p).lower() != "sample_menus.json"
    )


def load_menu_items_json() -> Tuple[OrderedDict, Dict[Tuple[str, str, str], DishPointer]]:
    """
    Returns:
      sections_payload:
        OrderedDict[str, list[dict]]
          section -> [{"name": cuisine, "dishes": [...]}, ...]
      dish_index:
        {(section, cuisine, dish_name): DishPointer(...)}
    """
    sections_payload: OrderedDict = OrderedDict()
    dish_index: Dict[Tuple[str, str, str], DishPointer] = {}

    for path in _json_files():
        with open(path, "r", encoding="utf-8") as f:
            payload = json.load(f)

        section_name = (payload.get("category") or "").strip()
        if not section_name:
            continue
        cuisines = payload.get("cuisines", [])
        if section_name not in sections_payload:
            sections_payload[section_name] = []

        for ci, cuisine in enumerate(cuisines):
            cuisine_name = (cuisine.get("name") or "General").strip()
            dishes = cuisine.get("dishes", []) or []
            sections_payload[section_name].append({
                "name": cuisine_name,
                "dishes": dishes,
            })
            for di, dish in enumerate(dishes):
                dish_name = (dish.get("name") or "").strip()
                if not dish_name:
                    continue
                dish_index[(section_name, cuisine_name, dish_name)] = DishPointer(
                    file_path=path,
                    cuisine_index=ci,
                    dish_index=di,
                )
    return sections_payload, dish_index


def _safe_write_json(path: str, payload: dict) -> None:
    tmp_path = f"{path}.tmp"
    with open(tmp_path, "w", encoding="utf-8") as f:
        json.dump(payload, f, indent=2, ensure_ascii=False)
    os.replace(tmp_path, path)


def update_master_dish_descriptions(
    pointer: DishPointer,
    short_description: Optional[str] = None,
    premium_description: Optional[str] = None,
) -> bool:
    try:
        with open(pointer.file_path, "r", encoding="utf-8") as f:
            payload = json.load(f)
    except (OSError, json.JSONDecodeError):
        return False

    cuisines = payload.get("cuisines", [])
    if pointer.cuisine_index >= len(cuisines):
        return False
    dishes = cuisines[pointer.cuisine_index].get("dishes", [])
    if pointer.dish_index >= len(dishes):
        return False

    target = dishes[pointer.dish_index]
    changed = False
    if short_description is not None and target.get("short_description") != short_description:
        target["short_description"] = short_description
        changed = True
    if premium_description is not None and target.get("premium_description") != premium_description:
        target["premium_description"] = premium_description
        changed = True

    if not changed:
        return False

    _safe_write_json(pointer.file_path, payload)
    return True
