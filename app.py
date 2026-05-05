"""
TCI Menu Craft — Streamlit App (Requirements-first flow)

Flow:
  Step 1 — Intake          : Sales person enters client requirements
  Step 2 — Suggestions     : Tool recommends top sample menus from the pool
  Step 3 — Customize       : Sales person tweaks dishes / adds live stations / add-ons
  Step 4 — Preview & PDF   : Final menu rendered + branded PDF generated
"""

import os
import base64
import csv
import json
from datetime import date
import streamlit as st
from collections import OrderedDict

from config import (
    COMPANY_NAME,
    LOGO_PATH,
    COLOR_PRIMARY,
    COLOR_ACCENT,
    MENU_ITEMS_DIR,
    CATEGORY_FILE_MAP,
    SECTION_CATEGORY_FILE_MAP,
)
from parser import parse_grid
from menu_loader import load_all, get_dishes
from pdf_generator import generate_pdf
from suggester import suggest

# Step 1 controlled options
OCCASION_OPTIONS = [
    "Wedding",
    "Reception",
    "Sangeet",
    "Mehendi",
    "Engagement",
    "Birthday",
    "Anniversary",
    "Corporate Dinner",
    "Conference",
    "Festive Celebration",
]
MENU_BUILD_MODES = ["Use suggested menu", "Create your own menu"]
DESCRIPTION_EDIT_SCOPES = ["This menu only", "Master data (backend)"]
MASTER_JSON_PATH = os.path.join("data", "pick_choose_menu.json")

# ── Page config ──────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="TCI Menu Craft",
    page_icon="🍽️",
    layout="wide",
)

# ── Custom CSS ───────────────────────────────────────────────────────────────
st.markdown(f"""
<style>
    .stApp {{ font-family: 'Segoe UI', sans-serif; }}
    .step-dot {{
        width: 36px; height: 36px; border-radius: 50%;
        display: flex; align-items: center; justify-content: center;
        font-weight: bold; font-size: 14px;
    }}
    .step-active  {{ background-color: {COLOR_PRIMARY}; color: white; }}
    .step-done    {{ background-color: {COLOR_ACCENT};  color: white; }}
    .step-pending {{ background-color: #E0E0E0;         color: #999; }}

    .section-header {{
        background-color: {COLOR_PRIMARY}; color: white;
        padding: 10px 16px; border-radius: 6px;
        margin-top: 16px; margin-bottom: 8px;
        font-size: 18px; font-weight: bold;
    }}
    .subcat-header {{
        color: {COLOR_PRIMARY}; font-weight: bold;
        border-bottom: 2px solid {COLOR_ACCENT};
        padding-bottom: 2px; margin-top: 12px;
    }}
    .summary-card {{
        background-color: #F5F0E8; padding: 12px;
        border-radius: 8px; border-left: 4px solid {COLOR_ACCENT};
        margin-bottom: 8px;
    }}
    .suggest-card {{
        background-color: #FFFFFF; padding: 16px;
        border: 1px solid #E0E0E0; border-left: 5px solid {COLOR_ACCENT};
        border-radius: 6px; margin-bottom: 12px;
    }}
    .badge {{
        display: inline-block; padding: 2px 10px;
        background: #F5F0E8; color: {COLOR_PRIMARY};
        border-radius: 12px; font-size: 11px; margin-right: 4px;
    }}
</style>
""", unsafe_allow_html=True)


# ── Session state defaults ───────────────────────────────────────────────────
def _init_state():
    defaults = {
        "step": 1,
        "grid_data": None,
        "all_items": None,
        "sample_menus": None,

        # Step 1 — intake
        "client_name": "",
        "event_title": "",
        "event_date": None,       # datetime.date (set via date picker)
        "venue": "",
        "occasion": OCCASION_OPTIONS[0],
        "diet": "veg",
        "meal": "dinner",
        "num_guests": "200",      # kept as free-text so there are no +/- steppers
        "is_series": False,
        "series_notes": "",
        "special_notes": "",

        # Step 2 — selected suggestion
        "selected_sample_id": None,
        "menu_type": None,
        "tier": None,
        "preferred_menu_type": None,
        "menu_build_mode": MENU_BUILD_MODES[0],
        "custom_targets": {},
        "description_edit_scope": DESCRIPTION_EDIT_SCOPES[0],

        # Step 3 — customisation
        "selections": {},
        "descriptions": {},
        "addons_text": "",

        # Step 4 — generated PDF state (so it survives Streamlit reruns)
        "generated_pdf_bytes": None,
        "generated_pdf_name": None,
    }
    for k, v in defaults.items():
        if k not in st.session_state:
            st.session_state[k] = v


_init_state()


# ── Load data (once) ─────────────────────────────────────────────────────────
@st.cache_data
def load_grid():
    return parse_grid()


@st.cache_data
def load_menu_items():
    return load_all()


@st.cache_data
def load_samples():
    from suggester import load_sample_menus
    return load_sample_menus()


if st.session_state.grid_data is None:
    st.session_state.grid_data = load_grid()
if st.session_state.all_items is None:
    st.session_state.all_items = load_menu_items()
if st.session_state.sample_menus is None:
    st.session_state.sample_menus = load_samples()

grid = st.session_state.grid_data
all_items = st.session_state.all_items
menu_types = grid["menu_types"]
if (
    st.session_state.preferred_menu_type is None
    and menu_types
):
    st.session_state.preferred_menu_type = next(iter(menu_types.keys()))


# ── Step indicator ───────────────────────────────────────────────────────────
def show_step_indicator():
    labels = ["Requirements", "Suggested Menu", "Customize", "Preview & PDF"]
    cols = st.columns(len(labels))
    for i, (col, label) in enumerate(zip(cols, labels), 1):
        if i < st.session_state.step:
            cls, icon = "step-done", "✓"
        elif i == st.session_state.step:
            cls, icon = "step-active", str(i)
        else:
            cls, icon = "step-pending", str(i)
        col.markdown(
            f'<div style="text-align:center">'
            f'<div class="step-dot {cls}" style="margin:auto">{icon}</div>'
            f'<div style="font-size:12px;margin-top:4px;color:#666">{label}</div>'
            f'</div>',
            unsafe_allow_html=True,
        )
    st.markdown("---")


# ── Header ───────────────────────────────────────────────────────────────────
col_logo, col_title = st.columns([1, 5])
with col_logo:
    if os.path.exists(LOGO_PATH):
        st.image(LOGO_PATH, width=80)
with col_title:
    st.markdown(f"## {COMPANY_NAME} — Menu Craft")
    st.caption("Capture client requirements → get a recommended menu → customise → export PDF")

show_step_indicator()


# ── Helper to apply a sample menu to session state ───────────────────────────
# ── Small helpers ────────────────────────────────────────────────────────────
def format_event_date(d):
    """Turn a datetime.date into a human-friendly string like '2nd Dec 2026'."""
    if not d:
        return ""
    day = d.day
    if 11 <= day <= 13:
        suffix = "th"
    else:
        suffix = {1: "st", 2: "nd", 3: "rd"}.get(day % 10, "th")
    return f"{day}{suffix} {d.strftime('%b %Y')}"


def parse_guest_count(text, fallback=0):
    """Extract an integer from free-text guest count input."""
    if text is None:
        return fallback
    try:
        return int(str(text).strip().replace(",", ""))
    except (ValueError, AttributeError):
        return fallback


def _available_pick_choose_headers(menu_types_data, all_items_data):
    """Return section->categories that have at least one dish loaded."""
    headers = OrderedDict()
    for _mt_name, mt_data in menu_types_data.items():
        for section, cats in mt_data.get("sections", {}).items():
            for category in cats.keys():
                dishes = get_dishes(all_items_data, section, category)
                if not dishes:
                    continue
                headers.setdefault(section, OrderedDict())
                headers[section][category] = True
    return headers


def _resolve_category_csv_file(section, category):
    if (section, category) in SECTION_CATEGORY_FILE_MAP:
        return SECTION_CATEGORY_FILE_MAP[(section, category)]
    return CATEGORY_FILE_MAP.get(category)


def _update_csv_master_description(section, category, dish_name, description):
    file_stub = _resolve_category_csv_file(section, category)
    if not file_stub:
        return False
    csv_path = os.path.join(MENU_ITEMS_DIR, f"{file_stub}.csv")
    if not os.path.exists(csv_path):
        return False

    changed = False
    rows = []
    with open(csv_path, "r", encoding="utf-8", newline="") as f:
        reader = csv.DictReader(f)
        fieldnames = list(reader.fieldnames or ["name", "description"])
        if "name" not in fieldnames:
            return False
        if "description" not in fieldnames:
            fieldnames.append("description")
        for row in reader:
            name = (row.get("name") or "").strip()
            if name == dish_name:
                row["description"] = description
                changed = True
            rows.append(row)

    if not changed:
        return False

    with open(csv_path, "w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)
    return True


def _update_json_master_description(section, category, dish_name, description):
    if not os.path.exists(MASTER_JSON_PATH):
        return False
    try:
        with open(MASTER_JSON_PATH, "r", encoding="utf-8") as f:
            payload = json.load(f)
    except (OSError, json.JSONDecodeError):
        return False

    changed = False
    section_block = payload.get("sections", {}).get(section, {})
    for dish in section_block.get(category, []):
        if dish.get("name") == dish_name:
            dish["short_description"] = description
            changed = True

    if not changed:
        return False

    with open(MASTER_JSON_PATH, "w", encoding="utf-8") as f:
        json.dump(payload, f, indent=2, ensure_ascii=False)
    return True


def maybe_persist_master_description(section, category, dish_name, description):
    csv_changed = _update_csv_master_description(section, category, dish_name, description)
    json_changed = _update_json_master_description(section, category, dish_name, description)
    return csv_changed or json_changed


def _normalize_dish_name(name):
    return " ".join((name or "").strip().lower().split())


def load_master_menu_json():
    if not os.path.exists(MASTER_JSON_PATH):
        return None
    try:
        with open(MASTER_JSON_PATH, "r", encoding="utf-8") as f:
            return json.load(f)
    except (OSError, json.JSONDecodeError):
        return None


def _menu_json_stats(payload):
    sections = payload.get("sections", {}) if isinstance(payload, dict) else {}
    section_count = len(sections)
    category_count = 0
    dish_count = 0
    duplicates = []

    for section, categories in sections.items():
        category_count += len(categories)
        for category, dishes in categories.items():
            seen = set()
            for dish in dishes:
                dish_count += 1
                norm = _normalize_dish_name(dish.get("name", ""))
                if not norm:
                    continue
                if norm in seen:
                    duplicates.append((section, category, dish.get("name", "")))
                else:
                    seen.add(norm)

    return {
        "section_count": section_count,
        "category_count": category_count,
        "dish_count": dish_count,
        "duplicates": duplicates,
    }


def dedupe_master_menu_json(payload):
    """De-duplicate dishes by normalized name within each category."""
    sections = payload.get("sections", {})
    removed = 0
    for _section, categories in sections.items():
        for _category, dishes in categories.items():
            uniq = {}
            for dish in dishes:
                key = _normalize_dish_name(dish.get("name", ""))
                if not key:
                    continue
                if key not in uniq:
                    uniq[key] = dish
                    continue
                # Keep richer descriptions when duplicates are found.
                existing = uniq[key]
                if len(dish.get("premium_description", "")) > len(existing.get("premium_description", "")):
                    existing["premium_description"] = dish.get("premium_description", existing.get("premium_description", ""))
                if len(dish.get("short_description", "")) > len(existing.get("short_description", "")):
                    existing["short_description"] = dish.get("short_description", existing.get("short_description", ""))
                removed += 1
            categories[_category] = list(uniq.values())
    return payload, removed


def apply_sample_menu(sample):
    """Pre-fill st.session_state.selections from a sample menu dict."""
    st.session_state.selected_sample_id = sample["id"]
    st.session_state.menu_type = sample["menu_type"]
    st.session_state.tier = sample["tier"]

    # Clear and re-seed selections
    st.session_state.selections = {}
    st.session_state.descriptions = {}
    for section, subcats in sample.get("selections", {}).items():
        for subcat, dish_names in subcats.items():
            key = f"sel_{section}_{subcat}"
            st.session_state.selections[key] = list(dish_names)
            # Pre-fill descriptions from CSV defaults
            dishes = get_dishes(all_items, section, subcat)
            dish_map = {d["name"]: d["description"] for d in dishes}
            for name in dish_names:
                desc_key = f"desc_{key}_{name}"
                st.session_state.descriptions[desc_key] = dish_map.get(name, "")


# ════════════════════════════════════════════════════════════════════════════
# STEP 1 — Requirements Intake
# ════════════════════════════════════════════════════════════════════════════
if st.session_state.step == 1:
    st.subheader("Step 1: Client Requirements")
    st.caption("Capture everything the client has told you. The tool will use this to suggest the closest matching menu from the sample pool.")

    # ── Client & event basics ────────────────────────────────────────────
    st.markdown("**Client & Event**")
    c1, c2, c3 = st.columns(3)
    with c1:
        st.session_state.client_name = st.text_input(
            "Client Name", value=st.session_state.client_name,
            placeholder="e.g. Mr. Mukesh Jain",
        )
    with c2:
        st.session_state.event_title = st.text_input(
            "Event Title", value=st.session_state.event_title,
            placeholder="e.g. Wedding Extravaganza",
        )
    with c3:
        occasion_index = (
            OCCASION_OPTIONS.index(st.session_state.occasion)
            if st.session_state.occasion in OCCASION_OPTIONS else 0
        )
        st.session_state.occasion = st.selectbox(
            "Occasion",
            OCCASION_OPTIONS,
            index=occasion_index,
        )

    c4, c5, c6 = st.columns(3)
    with c4:
        st.session_state.event_date = st.date_input(
            "Event Date",
            value=st.session_state.event_date,
            format="DD/MM/YYYY",
        )
    with c5:
        st.session_state.venue = st.text_input(
            "Venue", value=st.session_state.venue,
            placeholder="e.g. Gurgaon",
        )
    with c6:
        st.session_state.num_guests = st.text_input(
            "No. of Guests",
            value=str(st.session_state.num_guests or ""),
            placeholder="e.g. 400",
        )

    st.markdown("---")

    # ── Dietary & meal type ─────────────────────────────────────────────
    st.markdown("**Dietary preference & meal**")
    c7, c8, c9 = st.columns(3)
    with c7:
        diet_options = ["veg", "nonveg", "jain"]
        diet_labels = {"veg": "Vegetarian", "nonveg": "Non-Vegetarian", "jain": "Jain (no onion/garlic/root)"}
        st.session_state.diet = st.radio(
            "Dietary preference", diet_options,
            format_func=lambda d: diet_labels[d],
            index=diet_options.index(st.session_state.diet)
            if st.session_state.diet in diet_options else 0,
        )
    with c8:
        meal_options = ["breakfast", "lunch", "hi-tea", "dinner"]
        st.session_state.meal = st.radio(
            "Meal type", meal_options,
            format_func=lambda m: m.title(),
            index=meal_options.index(st.session_state.meal)
            if st.session_state.meal in meal_options else 3,
        )
    with c9:
        st.session_state.is_series = st.checkbox(
            "Series of events (multi-day)",
            value=st.session_state.is_series,
        )
        if st.session_state.is_series:
            st.session_state.series_notes = st.text_area(
                "Series details",
                value=st.session_state.series_notes,
                placeholder="e.g. Day 1 — Mehendi (lunch, 200), Day 2 — Sangeet (dinner, 400), Day 3 — Wedding (dinner, 600)",
                height=100,
            )

    st.markdown("---")
    st.markdown("**How do you want to build this menu?**")
    mode_index = (
        MENU_BUILD_MODES.index(st.session_state.menu_build_mode)
        if st.session_state.menu_build_mode in MENU_BUILD_MODES else 0
    )
    st.session_state.menu_build_mode = st.radio(
        "Build mode",
        MENU_BUILD_MODES,
        horizontal=True,
        index=mode_index,
        label_visibility="collapsed",
    )
    scope_index = (
        DESCRIPTION_EDIT_SCOPES.index(st.session_state.description_edit_scope)
        if st.session_state.description_edit_scope in DESCRIPTION_EDIT_SCOPES else 0
    )
    st.session_state.description_edit_scope = st.radio(
        "Description edit target",
        DESCRIPTION_EDIT_SCOPES,
        horizontal=True,
        index=scope_index,
        help="Choose whether description edits apply only to this menu or update backend master data.",
    )

    with st.expander("Pick & Choose JSON review utility", expanded=False):
        payload = load_master_menu_json()
        if not payload:
            st.info(
                "Master JSON not found yet. Generate it first using "
                "`python tools/build_pick_choose_json.py --pdf <path-to-pdf>`."
            )
        else:
            stats = _menu_json_stats(payload)
            c1, c2, c3 = st.columns(3)
            with c1:
                st.metric("Sections", stats["section_count"])
            with c2:
                st.metric("Categories", stats["category_count"])
            with c3:
                st.metric("Dishes", stats["dish_count"])

            dup_count = len(stats["duplicates"])
            if dup_count:
                st.warning(f"Found {dup_count} duplicate dish entries within categories.")
                preview = stats["duplicates"][:20]
                st.caption("Sample duplicates (first 20):")
                for section, category, dish_name in preview:
                    st.markdown(f"- `{section}` / `{category}` -> {dish_name}")
                if st.button("De-duplicate master JSON now", key="dedupe_master_json"):
                    cleaned, removed = dedupe_master_menu_json(payload)
                    with open(MASTER_JSON_PATH, "w", encoding="utf-8") as f:
                        json.dump(cleaned, f, indent=2, ensure_ascii=False)
                    st.success(f"Removed {removed} duplicates and saved `{MASTER_JSON_PATH}`.")
            else:
                st.success("No within-category duplicates detected.")

    # ── Special notes ─────────────────────────────────────────────────────
    st.session_state.special_notes = st.text_area(
        "Special notes / allergens / preferences (optional)",
        value=st.session_state.special_notes,
        placeholder="e.g. host prefers no mushrooms, 30 guests are gluten-free, requested live pasta station",
        height=80,
    )

    st.markdown("---")
    st.markdown("**Preferred menu type (from banquet grid)**")
    menu_type_names = list(menu_types.keys())
    if menu_type_names:
        mt_index = (
            menu_type_names.index(st.session_state.preferred_menu_type)
            if st.session_state.preferred_menu_type in menu_type_names else 0
        )
        st.session_state.preferred_menu_type = st.selectbox(
            "Menu Type",
            menu_type_names,
            index=mt_index,
            help="Loaded from Excel. Pricing shown below is source-of-truth from the banquet grid.",
        )

        selected_mt = menu_types[st.session_state.preferred_menu_type]
        pricing = selected_mt.get("pricing", {})
        if pricing:
            price_cols = st.columns(max(1, len(pricing)))
            for idx, (tier_name, tier_info) in enumerate(pricing.items()):
                with price_cols[idx]:
                    st.markdown(
                        f'<div class="summary-card"><b>{tier_name}</b><br/>₹{tier_info.get("price", 0)}/head<br/>MG {tier_info.get("mg", 0)}</div>',
                        unsafe_allow_html=True,
                    )
    else:
        st.warning("No menu types found in Excel grid.")

    if st.session_state.menu_build_mode == "Create your own menu":
        st.markdown("---")
        st.markdown("**Create-your-own headers (Pick & Choose source)**")
        st.caption(
            "Set item counts for the headers you want. "
            "Step 2 will let you choose exact dishes for each selected header."
        )
        pick_choose_headers = _available_pick_choose_headers(menu_types, all_items)
        if not pick_choose_headers:
            st.warning("No pick-and-choose headers could be resolved from loaded menu items.")
        else:
            for section, categories in pick_choose_headers.items():
                st.markdown(
                    f'<div class="section-header">{section}</div>',
                    unsafe_allow_html=True,
                )
                count_cols = st.columns(3)
                for idx, category in enumerate(categories.keys()):
                    qty_key = f"qty_{section}_{category}"
                    existing = int(st.session_state.custom_targets.get(qty_key, 0) or 0)
                    with count_cols[idx % 3]:
                        qty = st.number_input(
                            f"{category} (count)",
                            min_value=0,
                            max_value=20,
                            value=existing,
                            step=1,
                            key=f"ni_{qty_key}",
                        )
                        st.session_state.custom_targets[qty_key] = int(qty)

    st.markdown("---")
    col_a, col_b, col_c = st.columns([1, 5, 1])
    with col_c:
        if st.button("Get Suggestions →", type="primary", use_container_width=True):
            if not st.session_state.client_name.strip():
                st.error("Please enter the client name before proceeding.")
            elif not st.session_state.preferred_menu_type:
                st.error("Please select a menu type before proceeding.")
            elif (
                st.session_state.menu_build_mode == "Create your own menu"
                and sum(st.session_state.custom_targets.values()) <= 0
            ):
                st.error("Please select at least one header count for create-your-own menu.")
            else:
                st.session_state.step = 2
                st.rerun()


# ════════════════════════════════════════════════════════════════════════════
# STEP 2 — Suggested Menus
# ════════════════════════════════════════════════════════════════════════════
elif st.session_state.step == 2:
    if st.session_state.menu_build_mode == "Create your own menu":
        st.subheader("Step 2: Create Your Own Menu")
        st.caption("Pick exact dishes for each selected header from the pick-and-choose source.")

        preferred_menu_type = st.session_state.preferred_menu_type
        chosen_mt_pricing = menu_types.get(preferred_menu_type, {}).get("pricing", {})
        tier_options = list(chosen_mt_pricing.keys())
        if tier_options:
            default_tier_index = (
                tier_options.index(st.session_state.tier)
                if st.session_state.tier in tier_options else 0
            )
            st.session_state.tier = st.selectbox(
                "Choose price tier for this menu type",
                tier_options,
                index=default_tier_index,
            )

        selections_made = 0
        for qty_key, qty in st.session_state.custom_targets.items():
            if int(qty or 0) <= 0:
                continue
            _, section, category = qty_key.split("_", 2)
            dishes = get_dishes(all_items, section, category)
            if not dishes:
                continue

            st.markdown(
                f'<div class="subcat-header">{section} → {category} (pick up to {qty})</div>',
                unsafe_allow_html=True,
            )
            sel_key = f"sel_{section}_{category}"
            dish_names = [d["name"] for d in dishes]
            dish_map = {d["name"]: d["description"] for d in dishes}
            current = st.session_state.selections.get(sel_key, [])
            valid_current = [c for c in current if c in dish_names]
            selected = st.multiselect(
                f"Choose {category}",
                options=dish_names,
                default=valid_current,
                max_selections=int(qty),
                key=f"ms_custom_{sel_key}",
                label_visibility="collapsed",
            )
            st.session_state.selections[sel_key] = selected
            selections_made += len(selected)

            for dish_name in selected:
                desc_key = f"desc_{sel_key}_{dish_name}"
                default_desc = st.session_state.descriptions.get(
                    desc_key, dish_map.get(dish_name, "")
                )
                new_desc = st.text_input(
                    f"Description for {dish_name}",
                    value=default_desc,
                    key=f"ti_custom_{desc_key}",
                    label_visibility="collapsed",
                    placeholder=f"Description for {dish_name}",
                )
                st.session_state.descriptions[desc_key] = new_desc
                if (
                    st.session_state.description_edit_scope == "Master data (backend)"
                    and new_desc != dish_map.get(dish_name, "")
                ):
                    maybe_persist_master_description(section, category, dish_name, new_desc)

        st.markdown("---")
        col_a, col_b, col_c = st.columns([1, 5, 1])
        with col_a:
            if st.button("← Back", use_container_width=True):
                st.session_state.step = 1
                st.rerun()
        with col_c:
            if st.button("Preview & Export →", type="primary", use_container_width=True):
                if selections_made <= 0:
                    st.error("Please select at least one dish before continuing.")
                else:
                    st.session_state.menu_type = preferred_menu_type
                    st.session_state.step = 4
                    st.rerun()
    else:
        st.subheader("Step 2: Suggested Menus")
        st.caption("Top matches from the sample-menu pool. Pick the closest one — you'll be able to tweak it on the next screen.")

        requirements = {
            "diet": st.session_state.diet,
            "occasion": st.session_state.occasion,
            "meal": st.session_state.meal,
            "num_guests": parse_guest_count(st.session_state.num_guests),
        }
        preferred_menu_type = st.session_state.preferred_menu_type
        scored = suggest(requirements, top_n=None)
        suggestions = [
            (menu, score, reasons)
            for menu, score, reasons in scored
            if menu.get("menu_type") == preferred_menu_type
        ][:3]

        st.caption(f"Showing suggestions for selected menu type: **{preferred_menu_type}**")

        if not suggestions:
            st.warning(
                "No sample menus found for the selected menu type. "
                "You can still continue and edit selections manually."
            )
        else:
            for idx, (menu, score, reasons) in enumerate(suggestions):
                mt_pricing = menu_types.get(menu["menu_type"], {}).get("pricing", {})
                tier_info = mt_pricing.get(menu["tier"], {})
                price = tier_info.get("price", "?")
                mg = tier_info.get("mg", "?")

                badge = "TOP MATCH" if idx == 0 else f"OPTION {idx + 1}"
                st.markdown(
                    f'<div class="suggest-card">'
                    f'<div style="color:{COLOR_ACCENT};font-weight:bold;font-size:11px;letter-spacing:1px">'
                    f'{badge}  ·  match score {score:.0f}</div>'
                    f'<h3 style="margin:4px 0 6px 0;color:{COLOR_PRIMARY}">{menu["name"]}</h3>'
                    f'<div style="color:#555;margin-bottom:8px">{menu.get("description", "")}</div>'
                    f'<div style="margin-bottom:6px">'
                    + "".join(f'<span class="badge">{r}</span>' for r in reasons)
                    + f'</div>'
                    f'<div style="font-size:12px;color:#666">'
                    f'<b>Base:</b> {menu["menu_type"]} — {menu["tier"]} tier '
                    f'·  ₹{price}/head  ·  MG {mg} guests'
                    f'</div>'
                    f'</div>',
                    unsafe_allow_html=True,
                )

                cols = st.columns([6, 2])
                with cols[1]:
                    if st.button(f"Use this menu", key=f"pick_{menu['id']}", type="primary", use_container_width=True):
                        apply_sample_menu(menu)
                        st.session_state.step = 3
                        st.rerun()

        st.markdown("### Or continue directly to editing")
        chosen_mt_pricing = menu_types.get(preferred_menu_type, {}).get("pricing", {})
        tier_options = list(chosen_mt_pricing.keys())
        if tier_options:
            default_tier_index = (
                tier_options.index(st.session_state.tier)
                if st.session_state.tier in tier_options else 0
            )
            manual_tier = st.selectbox(
                "Choose price tier for this menu type",
                tier_options,
                index=default_tier_index,
            )
            if st.button("Skip suggestions and edit menu", use_container_width=False):
                st.session_state.selected_sample_id = None
                st.session_state.menu_type = preferred_menu_type
                st.session_state.tier = manual_tier
                st.session_state.selections = {}
                st.session_state.descriptions = {}
                st.session_state.step = 3
                st.rerun()
        else:
            st.warning("No pricing tiers found for selected menu type in Excel grid.")

        st.markdown("---")
        col_a, col_b, col_c = st.columns([1, 5, 1])
        with col_a:
            if st.button("← Back", use_container_width=True):
                st.session_state.step = 1
                st.rerun()


# ════════════════════════════════════════════════════════════════════════════
# STEP 3 — Customize
# ════════════════════════════════════════════════════════════════════════════
elif st.session_state.step == 3:
    st.subheader("Step 3: Customize the Menu")
    st.caption(
        f"Base: **{st.session_state.menu_type}** — **{st.session_state.tier}** tier. "
        "Add or remove dishes. Add-ons go at the bottom."
    )

    mt = menu_types[st.session_state.menu_type]

    # ── Sidebar summary ─────────────────────────────────────────────────
    with st.sidebar:
        st.markdown("### Menu Summary")
        total_selected = 0
        total_allowed = 0
        for section, cats in mt["sections"].items():
            sec_selected = 0
            sec_allowed = 0
            for cat, info in cats.items():
                if info["max"] > 0:
                    key = f"sel_{section}_{cat}"
                    count = len(st.session_state.selections.get(key, []))
                    sec_selected += count
                    sec_allowed += info["max"]
            if sec_allowed > 0:
                total_selected += sec_selected
                total_allowed += sec_allowed
                color = "green" if sec_selected > 0 else "gray"
                st.markdown(
                    f'<div style="margin-bottom:6px">'
                    f'<b>{section}</b><br/>'
                    f'<span style="color:{color}">'
                    f'{sec_selected} / {sec_allowed} items selected</span>'
                    f'</div>',
                    unsafe_allow_html=True,
                )
        st.markdown("---")
        st.markdown(f"**Total: {total_selected} / {total_allowed} items**")

    # ── Section by section ──────────────────────────────────────────────
    for section, cats in mt["sections"].items():
        active_cats = {c: v for c, v in cats.items() if v["max"] > 0}
        if not active_cats:
            continue

        st.markdown(
            f'<div class="section-header">{section}</div>',
            unsafe_allow_html=True,
        )

        for cat, info in active_cats.items():
            max_items = info["max"]
            dishes = get_dishes(all_items, section, cat)

            st.markdown(
                f'<div class="subcat-header">{cat} — Select up to {max_items}</div>',
                unsafe_allow_html=True,
            )

            key = f"sel_{section}_{cat}"

            if not dishes:
                st.warning(f"No dishes loaded for '{cat}'. Add items to the CSV.")
                continue

            dish_names = [d["name"] for d in dishes]
            dish_map = {d["name"]: d["description"] for d in dishes}

            current = st.session_state.selections.get(key, [])
            valid_current = [c for c in current if c in dish_names]

            selected = st.multiselect(
                f"Choose {cat}",
                options=dish_names,
                default=valid_current,
                max_selections=max_items,
                key=f"ms_{key}",
                label_visibility="collapsed",
            )
            st.session_state.selections[key] = selected

            for dish_name in selected:
                desc_key = f"desc_{key}_{dish_name}"
                default_desc = st.session_state.descriptions.get(
                    desc_key, dish_map.get(dish_name, "")
                )
                new_desc = st.text_input(
                    f"Description for {dish_name}",
                    value=default_desc,
                    key=f"ti_{desc_key}",
                    label_visibility="collapsed",
                    placeholder=f"Description for {dish_name}",
                )
                st.session_state.descriptions[desc_key] = new_desc
                if (
                    st.session_state.description_edit_scope == "Master data (backend)"
                    and new_desc != dish_map.get(dish_name, "")
                ):
                    maybe_persist_master_description(section, cat, dish_name, new_desc)

    # ── Optional Extras: categories beyond the base menu type ───────────
    # Build the union of every (section, category) across all menu types
    # so the sales person can add things the base menu type does not include.
    base_section_cats = {
        (s, c) for s, cats in mt["sections"].items() for c, info in cats.items() if info["max"] > 0
    }
    extras_by_section = OrderedDict()
    for _mt_name, _mt_data in menu_types.items():
        for s, cats in _mt_data["sections"].items():
            for c, info in cats.items():
                if info["max"] <= 0:
                    continue
                if (s, c) in base_section_cats:
                    continue
                extras_by_section.setdefault(s, set()).add(c)

    if extras_by_section:
        st.markdown(
            f'<div class="section-header">Optional Extras (add on top of base menu)</div>',
            unsafe_allow_html=True,
        )
        st.caption(
            "Anything not part of the chosen base menu type. Pick freely — these are added to the menu without enforcing a cap. "
            "Use this to bolt on a welcome drink, a live mocktail bar, chaats, a live station, etc."
        )
        with st.expander("Show optional extras", expanded=False):
            for section, cat_set in extras_by_section.items():
                st.markdown(
                    f'<div class="subcat-header" style="margin-top:14px">{section}</div>',
                    unsafe_allow_html=True,
                )
                for cat in sorted(cat_set):
                    dishes = get_dishes(all_items, section, cat)
                    if not dishes:
                        continue
                    key = f"sel_{section}_{cat}"
                    dish_names = [d["name"] for d in dishes]
                    dish_map = {d["name"]: d["description"] for d in dishes}

                    current = st.session_state.selections.get(key, [])
                    valid_current = [c for c in current if c in dish_names]

                    st.markdown(f"**{cat}** _(extra — no cap)_")
                    selected = st.multiselect(
                        f"Choose {cat}",
                        options=dish_names,
                        default=valid_current,
                        key=f"ms_extra_{key}",
                        label_visibility="collapsed",
                        placeholder=f"Optional — pick any {cat.lower()}",
                    )
                    st.session_state.selections[key] = selected

                    for dish_name in selected:
                        desc_key = f"desc_{key}_{dish_name}"
                        default_desc = st.session_state.descriptions.get(
                            desc_key, dish_map.get(dish_name, "")
                        )
                        new_desc = st.text_input(
                            f"Description for {dish_name}",
                            value=default_desc,
                            key=f"ti_extra_{desc_key}",
                            label_visibility="collapsed",
                            placeholder=f"Description for {dish_name}",
                        )
                        st.session_state.descriptions[desc_key] = new_desc
                        if (
                            st.session_state.description_edit_scope == "Master data (backend)"
                            and new_desc != dish_map.get(dish_name, "")
                        ):
                            maybe_persist_master_description(section, cat, dish_name, new_desc)

    # ── Add-ons / special requests ──────────────────────────────────────
    st.markdown(
        f'<div class="section-header">Add-ons & Special Requests</div>',
        unsafe_allow_html=True,
    )
    st.caption("Anything outside the standard menu — extra live stations, themed counters, allergen subs, custom desserts. This is shown verbatim on the PDF.")
    st.session_state.addons_text = st.text_area(
        "Add-ons",
        value=st.session_state.addons_text,
        placeholder="e.g.\n• Add Sushi Station for 100 guests (live counter)\n• Extra dessert: Tres Leches\n• Gluten-free thali for 30 guests",
        height=130,
        label_visibility="collapsed",
    )

    st.markdown("---")
    col1, col2, col3 = st.columns([1, 5, 1])
    with col1:
        if st.button("← Back", use_container_width=True):
            st.session_state.step = 2
            st.rerun()
    with col3:
        if st.button("Preview & Export →", type="primary", use_container_width=True):
            st.session_state.step = 4
            st.rerun()


# ════════════════════════════════════════════════════════════════════════════
# STEP 4 — Preview & Generate PDF
# ════════════════════════════════════════════════════════════════════════════
elif st.session_state.step == 4:
    st.subheader("Step 4: Preview & Generate PDF")

    # ── Build structured selections ──────────────────────────────────────
    # Walk the union of (section, category) across ALL menu types so any
    # extras the sales person picked beyond the base menu type are also
    # included in the PDF in their natural section position.
    mt = menu_types[st.session_state.menu_type]

    union_sections = OrderedDict()
    # Start with the base menu type's section/category order so that order is preserved.
    for section, cats in mt["sections"].items():
        union_sections[section] = OrderedDict()
        for cat, info in cats.items():
            if info["max"] > 0:
                union_sections[section][cat] = True
    # Then merge in any additional categories from other menu types.
    for _mt_name, _mt_data in menu_types.items():
        for section, cats in _mt_data["sections"].items():
            for cat, info in cats.items():
                if info["max"] <= 0:
                    continue
                union_sections.setdefault(section, OrderedDict())
                if cat not in union_sections[section]:
                    union_sections[section][cat] = True

    pdf_selections = OrderedDict()
    for section, cats in union_sections.items():
        section_dishes = OrderedDict()
        for cat in cats:
            key = f"sel_{section}_{cat}"
            selected_names = st.session_state.selections.get(key, [])
            if not selected_names:
                continue
            dishes_for_pdf = []
            for name in selected_names:
                desc_key = f"desc_{key}_{name}"
                desc = st.session_state.descriptions.get(desc_key, "")
                dishes_for_pdf.append({"name": name, "description": desc})
            section_dishes[cat] = dishes_for_pdf
        if section_dishes:
            pdf_selections[section] = section_dishes

    # ── Preview ──────────────────────────────────────────────────────────
    st.markdown("### Menu Preview")
    if not pdf_selections:
        st.warning("No items selected. Go back and customise the menu.")
    else:
        for section, subcats in pdf_selections.items():
            st.markdown(
                f'<div class="section-header">{section}</div>',
                unsafe_allow_html=True,
            )
            for subcat, dishes in subcats.items():
                st.markdown(f"**{subcat}**")
                for dish in dishes:
                    desc_text = f" — *{dish['description']}*" if dish["description"] else ""
                    st.markdown(f"- **{dish['name']}**{desc_text}")

    if st.session_state.addons_text.strip():
        st.markdown(
            f'<div class="section-header">Add-ons & Special Requests</div>',
            unsafe_allow_html=True,
        )
        for line in st.session_state.addons_text.strip().splitlines():
            if line.strip():
                st.markdown(f"- {line.strip().lstrip('•').strip()}")

    st.markdown("---")

    col1, col2, col3, col4 = st.columns([1, 2, 2, 1])

    with col1:
        if st.button("← Back", use_container_width=True):
            # Clear any previously generated PDF so it doesn't stick around
            st.session_state.generated_pdf_bytes = None
            st.session_state.generated_pdf_name = None
            st.session_state.step = 3
            st.rerun()

    with col3:
        generate_label = (
            "Regenerate PDF" if st.session_state.generated_pdf_bytes else "Generate PDF"
        )
        if st.button(generate_label, type="primary", use_container_width=True):
            if not pdf_selections:
                st.error("No items selected!")
            else:
                tier_info = mt["pricing"][st.session_state.tier]
                addon_lines = [
                    line.strip().lstrip("•").strip()
                    for line in st.session_state.addons_text.splitlines()
                    if line.strip()
                ]
                filepath = generate_pdf(
                    client_name=st.session_state.client_name,
                    event_date=format_event_date(st.session_state.event_date),
                    venue=st.session_state.venue,
                    menu_type_name=st.session_state.menu_type,
                    tier_name=st.session_state.tier,
                    tier_info=tier_info,
                    selections=pdf_selections,
                    event_title=st.session_state.event_title,
                    num_guests=parse_guest_count(st.session_state.num_guests),
                    addons=addon_lines,
                )
                with open(filepath, "rb") as f:
                    st.session_state.generated_pdf_bytes = f.read()
                st.session_state.generated_pdf_name = os.path.basename(filepath)
                st.rerun()

    # ── Inline PDF preview (persists across reruns via session_state) ────
    if st.session_state.generated_pdf_bytes:
        st.markdown("---")
        st.markdown("### PDF Preview")
        st.caption(
            f"**{st.session_state.generated_pdf_name}** — scroll through to review. "
            "If it looks good, use the download button below. "
            "Otherwise click ‘← Back’, tweak the menu, and regenerate."
        )
        b64 = base64.b64encode(st.session_state.generated_pdf_bytes).decode("utf-8")
        pdf_iframe = (
            f'<iframe src="data:application/pdf;base64,{b64}" '
            f'width="100%" height="820" '
            f'style="border:1px solid #E0E0E0;border-radius:6px" '
            f'type="application/pdf"></iframe>'
        )
        st.markdown(pdf_iframe, unsafe_allow_html=True)

        dl_col1, dl_col2, dl_col3 = st.columns([2, 2, 2])
        with dl_col2:
            st.download_button(
                label="⬇  Download PDF",
                data=st.session_state.generated_pdf_bytes,
                file_name=st.session_state.generated_pdf_name,
                mime="application/pdf",
                type="primary",
                use_container_width=True,
            )

    # ── Sidebar ──────────────────────────────────────────────────────────
    with st.sidebar:
        st.markdown("### Event Details")
        if st.session_state.client_name:
            st.write(f"**Client:** {st.session_state.client_name}")
        if st.session_state.event_title:
            st.write(f"**Event:** {st.session_state.event_title}")
        if st.session_state.event_date:
            st.write(f"**Date:** {format_event_date(st.session_state.event_date)}")
        if st.session_state.venue:
            st.write(f"**Venue:** {st.session_state.venue}")
        _g = parse_guest_count(st.session_state.num_guests)
        if _g:
            st.write(f"**Guests:** {_g}")
        st.write(f"**Diet:** {st.session_state.diet}")
        st.write(f"**Meal:** {st.session_state.meal}")
        st.markdown("---")
        st.write(f"**Base menu:** {st.session_state.menu_type}")
        st.write(f"**Tier:** {st.session_state.tier}")

        total = sum(
            len(dishes)
            for subcats in pdf_selections.values()
            for dishes in subcats.values()
        )
        st.markdown(f"**Total dishes:** {total}")

        st.markdown("---")
        if st.button("Start Over"):
            for k in list(st.session_state.keys()):
                del st.session_state[k]
            st.rerun()
