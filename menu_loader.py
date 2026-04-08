"""
TCI Menu Craft — Menu Item Loader
Reads CSV files from data/menu_items/ and returns dish options per category.
"""

import csv
import os
import logging

from config import MENU_ITEMS_DIR, CATEGORY_FILE_MAP, SECTION_CATEGORY_FILE_MAP

logger = logging.getLogger(__name__)


def _load_csv(filename):
    """Load a single CSV file and return list of {name, description} dicts."""
    filepath = os.path.join(MENU_ITEMS_DIR, f"{filename}.csv")
    if not os.path.exists(filepath):
        logger.warning(f"CSV not found: {filepath} — skipping")
        return []

    items = []
    with open(filepath, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            name = row.get("name", "").strip()
            desc = row.get("description", "").strip()
            if name:
                items.append({"name": name, "description": desc})
    return items


def load_all():
    """Load all menu items and return a lookup dict.

    Returns:
        {
            ("Starters (90 Minutes)", "Veg"): [{"name": ..., "description": ...}, ...],
            "Welcome Drink": [{"name": ..., "description": ...}, ...],
            ...
        }
    """
    data = {}

    # Section-aware categories first (Non Veg, Veg that appear in multiple sections)
    for (section, category), filename in SECTION_CATEGORY_FILE_MAP.items():
        data[(section, category)] = _load_csv(filename)

    # Simple category map
    for category, filename in CATEGORY_FILE_MAP.items():
        data[category] = _load_csv(filename)

    return data


def get_dishes(all_items, section, category):
    """Get dishes for a specific section + category combination.

    Lookup priority: section-aware key first, then plain category key.
    """
    key = (section, category)
    if key in all_items:
        return all_items[key]
    if category in all_items:
        return all_items[category]
    return []
