"""
TCI Menu Craft — Streamlit App
A step-by-step menu builder for The Catering Inc.
"""

import os
import streamlit as st
from collections import OrderedDict

from config import COMPANY_NAME, LOGO_PATH, COLOR_PRIMARY, COLOR_ACCENT
from parser import parse_grid
from menu_loader import load_all, get_dishes
from pdf_generator import generate_pdf

# ── Page config ──────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="TCI Menu Craft",
    page_icon="🍽️",
    layout="wide",
)

# ── Custom CSS ───────────────────────────────────────────────────────────────
st.markdown(f"""
<style>
    .stApp {{
        font-family: 'Segoe UI', sans-serif;
    }}
    .step-indicator {{
        display: flex;
        justify-content: center;
        gap: 8px;
        margin-bottom: 20px;
    }}
    .step-dot {{
        width: 36px;
        height: 36px;
        border-radius: 50%;
        display: flex;
        align-items: center;
        justify-content: center;
        font-weight: bold;
        font-size: 14px;
    }}
    .step-active {{
        background-color: {COLOR_PRIMARY};
        color: white;
    }}
    .step-done {{
        background-color: {COLOR_ACCENT};
        color: white;
    }}
    .step-pending {{
        background-color: #E0E0E0;
        color: #999;
    }}
    .section-header {{
        background-color: {COLOR_PRIMARY};
        color: white;
        padding: 10px 16px;
        border-radius: 6px;
        margin-top: 16px;
        margin-bottom: 8px;
        font-size: 18px;
        font-weight: bold;
    }}
    .subcat-header {{
        color: {COLOR_PRIMARY};
        font-weight: bold;
        border-bottom: 2px solid {COLOR_ACCENT};
        padding-bottom: 2px;
        margin-top: 12px;
    }}
    .summary-card {{
        background-color: #F5F0E8;
        padding: 12px;
        border-radius: 8px;
        border-left: 4px solid {COLOR_ACCENT};
        margin-bottom: 8px;
    }}
</style>
""", unsafe_allow_html=True)


# ── Session state defaults ───────────────────────────────────────────────────
def _init_state():
    defaults = {
        "step": 1,
        "grid_data": None,
        "all_items": None,
        "menu_type": None,
        "tier": None,
        "selections": {},
        "descriptions": {},
        "client_name": "",
        "event_date": "",
        "venue": "",
        "event_title": "",
        "num_guests": "",
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


if st.session_state.grid_data is None:
    st.session_state.grid_data = load_grid()
if st.session_state.all_items is None:
    st.session_state.all_items = load_menu_items()

grid = st.session_state.grid_data
all_items = st.session_state.all_items
menu_types = grid["menu_types"]


# ── Step indicator ───────────────────────────────────────────────────────────
def show_step_indicator():
    labels = ["Menu Type", "Price Tier", "Build Menu", "Preview & Export"]
    cols = st.columns(len(labels))
    for i, (col, label) in enumerate(zip(cols, labels), 1):
        if i < st.session_state.step:
            cls = "step-done"
            icon = "✓"
        elif i == st.session_state.step:
            cls = "step-active"
            icon = str(i)
        else:
            cls = "step-pending"
            icon = str(i)
        col.markdown(
            f'<div style="text-align:center">'
            f'<div class="step-dot {cls}" style="margin:auto">{icon}</div>'
            f'<div style="font-size:12px;margin-top:4px;color:#666">{label}</div>'
            f'</div>',
            unsafe_allow_html=True,
        )
    st.markdown("---")


# ── Header ───────────────────────────────────────────────────────────────────
col_logo, col_title = st.columns([1, 4])
with col_logo:
    if os.path.exists(LOGO_PATH):
        st.image(LOGO_PATH, width=80)
with col_title:
    st.markdown(f"## {COMPANY_NAME} — Menu Craft")
    st.caption("Build a customized banquet menu in minutes")

show_step_indicator()


# ════════════════════════════════════════════════════════════════════════════
# STEP 1 — Select Menu Type
# ════════════════════════════════════════════════════════════════════════════
if st.session_state.step == 1:
    st.subheader("Step 1: Select Menu Type")

    menu_type_names = list(menu_types.keys())
    selected = st.selectbox(
        "Choose a menu type",
        menu_type_names,
        index=menu_type_names.index(st.session_state.menu_type)
        if st.session_state.menu_type in menu_type_names else 0,
    )

    # Show preview of what's included
    if selected:
        mt = menu_types[selected]
        st.markdown("**What's included:**")
        for section, cats in mt["sections"].items():
            active = [f"{c} ({v['max']})" for c, v in cats.items() if v["max"] > 0]
            if active:
                st.markdown(f"- **{section}:** {', '.join(active)}")

        total = sum(
            v["max"] for cats in mt["sections"].values() for v in cats.values()
        )
        st.info(f"Total items in this menu: **{total}**")

    col1, col2 = st.columns([6, 1])
    with col2:
        if st.button("Next →", type="primary", use_container_width=True):
            st.session_state.menu_type = selected
            st.session_state.step = 2
            st.rerun()


# ════════════════════════════════════════════════════════════════════════════
# STEP 2 — Select Price Tier
# ════════════════════════════════════════════════════════════════════════════
elif st.session_state.step == 2:
    st.subheader("Step 2: Select Price Tier")

    mt = menu_types[st.session_state.menu_type]
    pricing = mt["pricing"]

    tier_options = list(pricing.keys())
    tier_labels = {
        "Desire": "Desire (Premium)",
        "Wish": "Wish (Standard)",
        "Walk": "Walk (Economy)",
    }

    selected_tier = st.radio(
        "Choose a pricing tier",
        tier_options,
        format_func=lambda t: tier_labels.get(t, t),
        index=tier_options.index(st.session_state.tier)
        if st.session_state.tier in tier_options else 0,
    )

    info = pricing[selected_tier]
    st.markdown(
        f'<div class="summary-card">'
        f'<b>₹{info["price"]}</b> per head &nbsp;|&nbsp; '
        f'Minimum guarantee: <b>{info["mg"]} guests</b>'
        f'</div>',
        unsafe_allow_html=True,
    )

    # Tier comparison table
    st.markdown("**All tiers for this menu:**")
    rows = []
    for t in tier_options:
        p = pricing[t]
        rows.append({
            "Tier": tier_labels.get(t, t),
            "Price / Head (₹)": p["price"],
            "Min. Guests": p["mg"],
        })
    st.table(rows)

    col1, col2, col3 = st.columns([1, 5, 1])
    with col1:
        if st.button("← Back", use_container_width=True):
            st.session_state.step = 1
            st.rerun()
    with col3:
        if st.button("Next →", type="primary", use_container_width=True):
            st.session_state.tier = selected_tier
            st.session_state.step = 3
            st.rerun()


# ════════════════════════════════════════════════════════════════════════════
# STEP 3 — Build Menu
# ════════════════════════════════════════════════════════════════════════════
elif st.session_state.step == 3:
    st.subheader("Step 3: Build Your Menu")
    st.caption(
        f"**{st.session_state.menu_type}** — "
        f"**{st.session_state.tier}** tier"
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
        st.markdown(
            f"**Total: {total_selected} / {total_allowed} items**"
        )

    # ── Main content — section by section ────────────────────────────────
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
                f'<div class="subcat-header">'
                f'{cat} — Select up to {max_items}</div>',
                unsafe_allow_html=True,
            )

            key = f"sel_{section}_{cat}"

            if not dishes:
                st.warning(f"No dishes loaded for '{cat}'. Add items to the CSV.")
                continue

            dish_names = [d["name"] for d in dishes]
            dish_map = {d["name"]: d["description"] for d in dishes}

            # Pre-select from session state
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

            # Editable descriptions
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

    st.markdown("---")
    col1, col2, col3 = st.columns([1, 5, 1])
    with col1:
        if st.button("← Back", use_container_width=True):
            st.session_state.step = 2
            st.rerun()
    with col3:
        if st.button("Next →", type="primary", use_container_width=True):
            st.session_state.step = 4
            st.rerun()


# ════════════════════════════════════════════════════════════════════════════
# STEP 4 — Preview & Generate PDF
# ════════════════════════════════════════════════════════════════════════════
elif st.session_state.step == 4:
    st.subheader("Step 4: Preview & Generate PDF")

    # Client details
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.session_state.client_name = st.text_input(
            "Client Name", value=st.session_state.client_name
        )
    with col2:
        st.session_state.event_date = st.text_input(
            "Event Date", value=st.session_state.event_date,
            placeholder="e.g. 15th March 2026",
        )
    with col3:
        st.session_state.venue = st.text_input(
            "Venue", value=st.session_state.venue
        )
    with col4:
        st.session_state.event_title = st.text_input(
            "Event Title (optional)",
            value=st.session_state.event_title,
            placeholder="e.g. Wedding Dinner",
        )

    st.markdown("---")

    # ── Build structured selections for PDF ──────────────────────────────
    mt = menu_types[st.session_state.menu_type]
    pdf_selections = OrderedDict()

    for section, cats in mt["sections"].items():
        section_dishes = OrderedDict()
        for cat, info in cats.items():
            if info["max"] == 0:
                continue
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
        st.warning("No items selected. Go back and build your menu.")
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

    st.markdown("---")

    # ── Generate PDF ─────────────────────────────────────────────────────
    col1, col2, col3, col4 = st.columns([1, 2, 2, 1])

    with col1:
        if st.button("← Back", use_container_width=True):
            st.session_state.step = 3
            st.rerun()

    with col3:
        if st.button("Generate PDF", type="primary", use_container_width=True):
            if not pdf_selections:
                st.error("No items selected!")
            else:
                tier_info = mt["pricing"][st.session_state.tier]
                filepath = generate_pdf(
                    client_name=st.session_state.client_name,
                    event_date=st.session_state.event_date,
                    venue=st.session_state.venue,
                    menu_type_name=st.session_state.menu_type,
                    tier_name=st.session_state.tier,
                    tier_info=tier_info,
                    selections=pdf_selections,
                    event_title=st.session_state.event_title,
                )
                st.success(f"PDF generated: {os.path.basename(filepath)}")

                with open(filepath, "rb") as f:
                    st.download_button(
                        label="Download PDF",
                        data=f.read(),
                        file_name=os.path.basename(filepath),
                        mime="application/pdf",
                        type="primary",
                    )

    # ── Sidebar info ─────────────────────────────────────────────────────
    with st.sidebar:
        st.markdown("### Event Details")
        st.write(f"**Menu:** {st.session_state.menu_type}")
        st.write(f"**Tier:** {st.session_state.tier}")
        if st.session_state.client_name:
            st.write(f"**Client:** {st.session_state.client_name}")
        if st.session_state.event_date:
            st.write(f"**Date:** {st.session_state.event_date}")
        if st.session_state.venue:
            st.write(f"**Venue:** {st.session_state.venue}")

        # Count
        total = sum(
            len(dishes)
            for subcats in pdf_selections.values()
            for dishes in subcats.values()
        )
        st.markdown(f"**Total items selected:** {total}")

        st.markdown("---")
        if st.button("Start Over"):
            for k in list(st.session_state.keys()):
                del st.session_state[k]
            st.rerun()
