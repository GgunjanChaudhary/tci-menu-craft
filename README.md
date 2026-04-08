# TCI Menu Craft

Menu generator for **The Catering Inc.** — a Streamlit-based tool that lets the sales team build customized banquet menus and export branded PDFs for clients.

## Setup

```bash
# Install dependencies
pip install -r requirements.txt

# Run the app
streamlit run app.py
```

## How It Works

1. **Select Menu Type** — Choose from 8 menu types (Corporate, Social Silver/Gold/Platinum, Veg/Non-Veg)
2. **Select Price Tier** — Desire (Premium), Wish (Standard), or Walk (Economy)
3. **Build Menu** — Pick dishes from each category within the allowed limits
4. **Preview & Export** — Enter client details and generate a branded PDF

## File Structure

- `app.py` — Streamlit wizard UI
- `parser.py` — Reads Excel grid (pricing + selection limits)
- `menu_loader.py` — Loads dish options from CSVs
- `pdf_generator.py` — Generates branded PDF using ReportLab
- `config.py` — All mappings, company info, paths
- `data/TCI_Banquet_Grid.xlsx` — Master pricing grid
- `data/menu_items/*.csv` — Dish lists (name, description)
- `assets/logo.png` — Company logo
- `output/` — Generated PDFs

## Customization

- **New menu type** → Update Excel only
- **New dish** → Update the relevant CSV only
- **New subcategory** → Add one CSV + one line in `config.py`
- **Replace logo** → Drop your PNG into `assets/logo.png`
