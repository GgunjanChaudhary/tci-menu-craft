"""
TCI Menu Craft — Configuration
All mappings, company info, and paths live here.
"""

import os

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# ── Paths ────────────────────────────────────────────────────────────────────
LOGO_PATH = os.path.join(BASE_DIR, "assets", "logo.png")
EXCEL_PATH = os.path.join(BASE_DIR, "data", "TCI_Banquet_Grid.xlsx")
MENU_ITEMS_DIR = os.path.join(BASE_DIR, "data", "menu_items")
SAMPLE_MENUS_PATH = os.path.join(BASE_DIR, "data", "sample_menus.json")
OUTPUT_DIR = os.path.join(BASE_DIR, "output")

# ── Company Info ─────────────────────────────────────────────────────────────
COMPANY_NAME = "The Catering Inc."
TAGLINE = "Let's celebrate events"

ABOUT_US = (
    '"The Catering Inc.", is a company managed and run by '
    '"Chef Gautam Chaudhry". Chef Gautam is well recognized for his bold '
    "flavors and progressive cuisine concepts and carries more than 2 decades "
    "of experience. During his working tenure, he has served some top hotels "
    "like Oberoi's, Hyatt, Radisson, etc at various leadership positions.\n\n"
    "Celebrations infuse life with passion and purpose but at "
    '"The Catering Inc.", we handcraft them with love. We understand how '
    "important this day is for you and we wish to put forward a memory you "
    "would cherish for a lifetime. We provide 360 degree holistic service "
    "where we take care of your food, its plating, Food Décor, Service, "
    "Crockery, Cutlery, right temperature at which food is served and "
    "presented, and things that matter.\n\n"
    "From menu designing to keeping it up with latest food trends to making "
    "sure we take care of guests with allergens and specific dietary "
    "requirements — We do it all."
)

# ── PDF Settings ─────────────────────────────────────────────────────────────
SHOW_PRICE_ON_PDF = False
SHOW_TIER_ON_PDF = False

# Section intro paragraphs (printed below each section header on the menu pages,
# matching the style of the sample Word menus). Sections not listed here render
# without an intro paragraph.
SECTION_INTROS = {
    "Break-up": (
        "Good drinks not only jazz up and prepare your guests for the food to "
        "come, they also brighten the mood and add to the zing. If served at "
        "correct temperature, they satiate the thirst and cleanse the palette "
        "for the gastronomical journey to follow."
    ),
    "Starters (90 Minutes)": (
        "Starters are the prelude to the meal — bite-sized creations crafted "
        "to tease the palate and set the tone for the indulgence to follow. "
        "From classic kebabs to contemporary global bites, each plate is "
        "designed to leave your guests craving for more."
    ),
    "Main Course": (
        "The heart of any celebration — our main course is a curated journey "
        "through robust flavors, slow-cooked gravies, fragrant rice and "
        "freshly baked breads. Every dish is plated with care and served at "
        "the right temperature to honour the occasion."
    ),
}

# Brand colors
COLOR_PRIMARY = "#6B2737"    # deep maroon
COLOR_ACCENT = "#C9A84C"     # gold
COLOR_TEXT = "#1A1A1A"        # near-black

# ── Category → CSV file mapping ──────────────────────────────────────────────
# For subcategories that appear only once across all sections
CATEGORY_FILE_MAP = {
    "Welcome Drink":           "welcome_drink",
    "Aerated Beverages":       "aerated_beverages",
    "Live Mocktail Bar":       "live_mocktail_bar",
    "Salads":                  "starters_salads",
    "Soups":                   "starters_soups",
    "Western Bread":           "starters_western_bread",
    "Chaats":                  "starters_chaats",
    "Paneer":                  "main_paneer",
    "Dal":                     "main_dal",
    "Starch":                  "main_starch",
    "Achaar/ Papad/ Chutney":  "main_achaar_papad",
    "Yoghurt/ Curd rice":      "main_yoghurt_curd",
    "Indian Breads":           "main_indian_breads",
    "Desserts":                "main_desserts",
    "Desserts Live":           "main_desserts_live",
    "Live Station":            "main_live_station",
}

# For subcategories that repeat across sections (Non Veg, Veg)
SECTION_CATEGORY_FILE_MAP = {
    ("Starters (90 Minutes)", "Non Veg"): "starters_nonveg",
    ("Starters (90 Minutes)", "Veg"):     "starters_veg",
    ("Main Course", "Non Veg"):           "main_nonveg",
    ("Main Course", "Veg"):               "main_veg",
}

# ── Excel grid layout constants ──────────────────────────────────────────────
EXCEL_SHEET = "Sheet2"
MENU_TYPE_ROW = 6          # row containing menu type names (1-indexed)
PRICE_ROWS = {
    "Desire": 8,
    "Wish": 9,
    "Walk": 10,
}
MG_ROW = 11
DATA_START_ROW = 13        # first section header row
DATA_END_ROW = 35          # last subcategory row (before Total Items)
NOTES_START_ROW = 38       # "Notes:" label row
MENU_TYPE_START_COL = 2    # column B (1-indexed)
