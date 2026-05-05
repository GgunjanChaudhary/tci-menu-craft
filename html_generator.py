"""
HTML generator for custom menu preview/export.
"""

from __future__ import annotations

import base64
import os
from html import escape

from config import COMPANY_NAME, TAGLINE, COLOR_PRIMARY, COLOR_ACCENT, COLOR_TEXT


def _logo_data_uri(logo_path: str) -> str:
    if not logo_path or not os.path.exists(logo_path):
        return ""
    with open(logo_path, "rb") as f:
        b64 = base64.b64encode(f.read()).decode("utf-8")
    return f"data:image/png;base64,{b64}"


def generate_menu_html(client_meta: dict, sections_payload: list, logo_path: str) -> str:
    logo_uri = _logo_data_uri(logo_path)
    title = escape(client_meta.get("event_title") or "Custom Menu")
    client = escape(client_meta.get("client_name") or "")
    venue = escape(client_meta.get("venue") or "")
    event_date = escape(client_meta.get("event_date") or "")

    sections_html = []
    for section in sections_payload:
        cuisines_html = []
        for cuisine in section.get("cuisines", []):
            dishes_html = []
            for dish in cuisine.get("dishes", []):
                dishes_html.append(
                    f"""
                    <div class="dish">
                      <div class="dish-name">{escape(dish.get("name", ""))}</div>
                      <div class="dish-desc">{escape(dish.get("description", ""))}</div>
                    </div>
                    """
                )
            cuisines_html.append(
                f"""
                <div class="cuisine">
                  <div class="cuisine-name">{escape(cuisine.get("name", ""))}</div>
                  {''.join(dishes_html)}
                </div>
                """
            )

        sections_html.append(
            f"""
            <section class="menu-section">
              <h2>{escape(section.get("name", ""))}</h2>
              <hr />
              {''.join(cuisines_html)}
            </section>
            """
        )

    logo_html = f'<img class="logo" src="{logo_uri}" alt="logo" />' if logo_uri else ""
    return f"""
<!doctype html>
<html>
<head>
  <meta charset="utf-8"/>
  <meta name="viewport" content="width=device-width, initial-scale=1"/>
  <title>{title}</title>
  <style>
    :root {{
      --primary: {COLOR_PRIMARY};
      --accent: {COLOR_ACCENT};
      --text: {COLOR_TEXT};
    }}
    body {{
      margin: 0;
      font-family: "Times New Roman", Georgia, serif;
      color: var(--text);
      background: #fff;
      padding: 28px 36px;
    }}
    .header {{
      display: flex;
      justify-content: space-between;
      align-items: center;
      border-bottom: 2px solid var(--accent);
      padding-bottom: 12px;
      margin-bottom: 18px;
    }}
    .logo {{ width: 72px; height: 72px; object-fit: contain; }}
    .brand {{ text-align: right; }}
    .company {{ font-size: 26px; color: var(--primary); font-weight: 700; }}
    .tagline {{ font-style: italic; color: var(--accent); }}
    .meta {{ margin: 14px 0 20px; text-align: center; }}
    .meta .title {{ font-size: 28px; color: var(--primary); font-weight: 700; margin-bottom: 8px; }}
    .menu-section {{ margin-bottom: 20px; }}
    .menu-section h2 {{
      margin: 0;
      font-size: 21px;
      color: var(--primary);
      text-transform: uppercase;
    }}
    .menu-section hr {{ border: none; border-top: 1px solid var(--accent); margin: 5px 0 10px; }}
    .cuisine-name {{ color: var(--primary); font-size: 17px; font-weight: 700; margin: 10px 0 6px; }}
    .dish {{ margin-bottom: 7px; }}
    .dish-name {{ text-align: right; font-weight: 700; font-size: 15px; }}
    .dish-desc {{ text-align: right; font-style: italic; color: #777; font-size: 13px; }}
  </style>
</head>
<body>
  <div class="header">
    {logo_html}
    <div class="brand">
      <div class="company">{escape(COMPANY_NAME)}</div>
      <div class="tagline">{escape(TAGLINE)}</div>
    </div>
  </div>
  <div class="meta">
    <div class="title">{title}</div>
    <div><b>Hosted by:</b> {client} &nbsp; | &nbsp; <b>Venue:</b> {venue} &nbsp; | &nbsp; <b>Date:</b> {event_date}</div>
  </div>
  {''.join(sections_html)}
</body>
</html>
"""
