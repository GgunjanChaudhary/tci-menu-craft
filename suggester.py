"""
TCI Menu Craft — Sample Menu Suggester
Loads the sample-menu pool and scores each candidate against client requirements.
"""

import json
from config import SAMPLE_MENUS_PATH


# ── Loading ──────────────────────────────────────────────────────────────────
def load_sample_menus(path=None):
    """Load all sample menus from the JSON pool."""
    path = path or SAMPLE_MENUS_PATH
    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)
    return data.get("menus", [])


# ── Scoring ──────────────────────────────────────────────────────────────────
def _score(menu, requirements):
    """Score a single sample menu against the requirements dict.

    Higher score = better match. Hard mismatches (diet conflict) are heavily
    penalised so they sink to the bottom but are still shown.
    """
    tags = menu.get("tags", {})
    score = 0.0
    reasons = []

    # ── Diet (hard constraint, high weight) ──────────────────────────────
    req_diet = requirements.get("diet")  # "veg" / "nonveg" / "jain"
    menu_diet = tags.get("diet")
    jain_ok = tags.get("jain_friendly", False)

    if req_diet == "jain":
        if jain_ok:
            score += 50
            reasons.append("Jain-friendly")
        elif menu_diet == "veg":
            score += 10
            reasons.append("Vegetarian (Jain adaptable)")
        else:
            score -= 100
            reasons.append("Not Jain-compatible")
    elif req_diet == "veg":
        if menu_diet == "veg":
            score += 40
            reasons.append("Vegetarian")
        else:
            score -= 80
            reasons.append("Contains non-veg")
    elif req_diet == "nonveg":
        if menu_diet == "nonveg":
            score += 40
            reasons.append("Non-vegetarian")
        else:
            score += 5  # veg menu is acceptable for nonveg client, just less ideal
            reasons.append("Vegetarian (could add non-veg)")

    # ── Occasion (substring/keyword overlap) ─────────────────────────────
    req_occ = (requirements.get("occasion") or "").strip().lower()
    if req_occ:
        menu_occs = [o.lower() for o in tags.get("occasion", [])]
        if any(req_occ == o for o in menu_occs):
            score += 30
            reasons.append(f"Matches '{req_occ}'")
        elif any(req_occ in o or o in req_occ for o in menu_occs):
            score += 18
            reasons.append(f"Similar to '{req_occ}'")
        # Common keyword bridges
        bridges = {
            "wedding": ["reception", "sangeet", "mehendi", "anniversary"],
            "corporate": ["conference", "business lunch", "office party", "client dinner"],
            "birthday": ["social", "anniversary"],
        }
        for key, related in bridges.items():
            if key in req_occ and any(r in menu_occs for r in related):
                score += 6

    # ── Meal type ────────────────────────────────────────────────────────
    req_meal = (requirements.get("meal") or "").lower()
    menu_meals = [m.lower() for m in tags.get("meal", [])]
    if req_meal and req_meal in menu_meals:
        score += 15
        reasons.append(f"Suited to {req_meal}")
    elif req_meal and menu_meals:
        score -= 4

    # ── Guest count fit ──────────────────────────────────────────────────
    req_guests = requirements.get("num_guests")
    if isinstance(req_guests, (int, float)) and req_guests > 0:
        gmin = tags.get("guest_min", 0)
        gmax = tags.get("guest_max", 10**6)
        if gmin <= req_guests <= gmax:
            score += 20
            reasons.append(f"Sized for {int(req_guests)} guests")
        else:
            # Distance-based soft penalty
            if req_guests < gmin:
                gap = (gmin - req_guests) / max(gmin, 1)
            else:
                gap = (req_guests - gmax) / max(gmax, 1)
            penalty = min(20, gap * 25)
            score -= penalty
            if req_guests < gmin:
                reasons.append(f"Sized larger than {int(req_guests)} guests")
            else:
                reasons.append(f"Sized smaller than {int(req_guests)} guests")

    return score, reasons


def suggest(requirements, top_n=3, path=None):
    """Return the top-N sample menus matching the given requirements.

    Args:
        requirements: dict with keys
            diet     — "veg" | "nonveg" | "jain"
            occasion — free-text string
            meal     — "breakfast" | "lunch" | "dinner" | "hi-tea" | ""
            num_guests — int

    Returns:
        list of (menu_dict, score, reasons) tuples sorted best-first.
    """
    menus = load_sample_menus(path)
    scored = []
    for m in menus:
        score, reasons = _score(m, requirements)
        scored.append((m, score, reasons))

    scored.sort(key=lambda x: x[1], reverse=True)
    return scored[:top_n] if top_n else scored
