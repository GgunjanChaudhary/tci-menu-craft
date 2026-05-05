"""
Build a multi-layer dish JSON from a Pick & Choose PDF.

Output schema:
{
  "source_file": "...",
  "sections": {
    "Section Name": {
      "Category Name": [
        {
          "name": "Dish",
          "short_description": "...",
          "premium_description": "..."
        }
      ]
    }
  }
}
"""

import argparse
import json
import re
from pathlib import Path


KNOWN_SECTIONS = {
    "BREAK-UP": "Break-up",
    "STARTERS": "Starters (90 Minutes)",
    "VEGETARIAN STARTERS": "Vegetarian Starters",
    "NON VEGETARIAN STARTERS": "Non Vegetarian Starters",
    "SALAD BAR": "Salad Bar",
    "SOUPS": "Soups",
    "MAIN COURSE": "Main Course",
    "DESSERTS": "Desserts",
    "LIVE STATIONS": "Live Stations",
    "BREADS": "Breads",
    "BEVERAGES": "Beverages",
}

KNOWN_CATEGORIES = {
    "INDIAN": "Indian",
    "ORIENTAL": "Oriental",
    "CONTINENTAL": "Continental",
    "WESTERN": "Western",
    "MEXICAN": "Mexican",
    "THAI": "Thai",
    "ITALIAN": "Italian",
    "CHINESE": "Chinese",
    "NORTH INDIAN": "North Indian",
    "SOUTH INDIAN": "South Indian",
}

KNOWN_SUBCATEGORIES = {
    "FISH": "Fish",
    "LAMB": "Lamb",
    "CHICKEN": "Chicken",
    "SEA FOOD": "Sea Food",
    "SEAFOOD": "Sea Food",
    "MUTTON": "Mutton",
    "VEG": "Veg",
    "VEGETARIAN": "Veg",
    "NON VEG": "Non Veg",
}


def _normalize(line: str) -> str:
    return re.sub(r"\s+", " ", line.strip()).upper()


def _titleize(line: str) -> str:
    line = re.sub(r"\s+", " ", line.strip(" :")).strip()
    return line.title()


def _short_description(name: str) -> str:
    return f"A flavorful preparation of {name.lower()} crafted for event menus."


def _premium_description(name: str) -> str:
    return (
        f"Chef-curated {name.lower()} finished with refined seasoning and "
        f"presented in a premium banquet style."
    )


def _read_pdf_text(pdf_path: Path) -> list[str]:
    try:
        from pypdf import PdfReader  # type: ignore
    except ImportError as exc:
        raise RuntimeError(
            "Missing dependency: pypdf. Install with `pip install pypdf`."
        ) from exc

    reader = PdfReader(str(pdf_path))
    lines: list[str] = []
    for page in reader.pages:
        text = page.extract_text() or ""
        lines.extend(text.splitlines())
    return [ln.strip() for ln in lines if ln and ln.strip()]


def parse_pick_choose(lines: list[str]) -> dict:
    sections: dict = {}
    current_section = "Uncategorized"
    current_category = "General"
    current_subcategory = ""
    sections.setdefault(current_section, {})
    sections[current_section].setdefault(current_category, [])

    for raw in lines:
        line = raw.strip(" -•\t")
        if not line:
            continue
        normalized = _normalize(line)

        if normalized.endswith(":"):
            normalized = normalized[:-1].strip()

        if normalized in KNOWN_SECTIONS:
            current_section = KNOWN_SECTIONS[normalized]
            sections.setdefault(current_section, {})
            current_category = "General"
            current_subcategory = ""
            sections[current_section].setdefault(current_category, [])
            continue

        if normalized in KNOWN_CATEGORIES:
            current_category = KNOWN_CATEGORIES[normalized]
            sections.setdefault(current_section, {})
            sections[current_section].setdefault(current_category, [])
            current_subcategory = ""
            continue

        if normalized in KNOWN_SUBCATEGORIES:
            current_subcategory = KNOWN_SUBCATEGORIES[normalized]
            sections.setdefault(current_section, {})
            merged_category = f"{current_category} - {current_subcategory}"
            sections[current_section].setdefault(merged_category, [])
            continue

        if (
            len(line) <= 40
            and line.endswith(":")
            and re.search(r"[A-Za-z]", line)
        ):
            current_section = _titleize(line)
            sections.setdefault(current_section, {})
            current_category = "General"
            current_subcategory = ""
            sections[current_section].setdefault(current_category, [])
            continue

        if (
            len(line.split()) <= 3
            and line.isalpha()
            and line == line.title()
        ):
            current_category = _titleize(line)
            current_subcategory = ""
            sections.setdefault(current_section, {})
            sections[current_section].setdefault(current_category, [])
            continue

        if re.fullmatch(r"[0-9\W]+", line):
            continue

        final_category = current_category
        if current_subcategory:
            final_category = f"{current_category} - {current_subcategory}"

        dish = {
            "name": line,
            "short_description": _short_description(line),
            "premium_description": _premium_description(line),
        }
        sections[current_section].setdefault(final_category, [])
        sections[current_section][final_category].append(dish)

    clean_sections = {}
    for section, categories in sections.items():
        clean_categories = {k: v for k, v in categories.items() if v}
        if clean_categories:
            clean_sections[section] = clean_categories
    return clean_sections


def main() -> None:
    parser = argparse.ArgumentParser(description="Build layered JSON from Pick & Choose PDF")
    parser.add_argument("--pdf", required=True, help="Path to Pick & Choose PDF")
    parser.add_argument(
        "--out",
        default="data/pick_choose_menu.json",
        help="Output JSON path (default: data/pick_choose_menu.json)",
    )
    args = parser.parse_args()

    pdf_path = Path(args.pdf)
    if not pdf_path.exists():
        raise FileNotFoundError(f"PDF not found: {pdf_path}")

    lines = _read_pdf_text(pdf_path)
    sections = parse_pick_choose(lines)
    payload = {
        "source_file": str(pdf_path),
        "sections": sections,
    }

    out_path = Path(args.out)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with out_path.open("w", encoding="utf-8") as f:
        json.dump(payload, f, indent=2, ensure_ascii=False)

    print(f"Wrote {out_path} with {len(sections)} sections.")


if __name__ == "__main__":
    main()
