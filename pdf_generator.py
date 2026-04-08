"""
TCI Menu Craft — PDF Generator v2
Landscape A4, elegant typography matching TCI sample menu style:
  - Section headers LEFT-aligned with gold rule
  - Dish names RIGHT-aligned (bold)
  - Dish descriptions RIGHT-aligned (grey italic)
  - Running page header with logo + company info
"""

import os
from reportlab.lib.pagesizes import A4, landscape
from reportlab.lib.units import inch, mm
from reportlab.lib.colors import HexColor
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT, TA_JUSTIFY
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Image, PageBreak, KeepTogether,
)
from reportlab.platypus.flowables import HRFlowable

from config import (
    COMPANY_NAME, TAGLINE, ABOUT_US, LOGO_PATH, OUTPUT_DIR,
    COLOR_PRIMARY, COLOR_ACCENT, COLOR_TEXT,
    SHOW_PRICE_ON_PDF, SHOW_TIER_ON_PDF,
)

# ── Colors ────────────────────────────────────────────────────────────────────
PRIMARY    = HexColor(COLOR_PRIMARY)   # deep maroon #6B2737
ACCENT     = HexColor(COLOR_ACCENT)    # gold  #C9A84C
TEXT_COLOR = HexColor(COLOR_TEXT)      # near-black
GREY       = HexColor("#808080")       # dish description grey

# ── Page geometry ─────────────────────────────────────────────────────────────
PAGE = landscape(A4)
PW, PH = PAGE        # ~841 x 595 pts (landscape)

LM = 25 * mm         # left margin
RM = 25 * mm         # right margin
TM = 36 * mm         # top margin — header drawn above this line
BM = 22 * mm         # bottom margin
CW = PW - LM - RM   # usable content width (~700 pts)


# ── Styles ────────────────────────────────────────────────────────────────────
def _build_styles():
    s = getSampleStyleSheet()

    def add(name, **kw):
        s.add(ParagraphStyle(name, parent=s["Normal"], **kw))

    # Cover page
    add("CoverCompany",
        fontName="Times-Bold", fontSize=26, textColor=PRIMARY,
        alignment=TA_CENTER, spaceBefore=6, spaceAfter=16)
    add("CoverTagline",
        fontName="Times-Italic", fontSize=13, textColor=ACCENT,
        alignment=TA_CENTER, spaceBefore=0, spaceAfter=14)
    add("EventTitle",
        fontName="Times-Bold", fontSize=20, textColor=TEXT_COLOR,
        alignment=TA_CENTER, spaceBefore=8, spaceAfter=6)
    add("CoverDetail",
        fontName="Times-Bold", fontSize=12, textColor=TEXT_COLOR,
        alignment=TA_CENTER, spaceAfter=3)
    add("AboutUs",
        fontName="Times-Roman", fontSize=10, textColor=TEXT_COLOR,
        alignment=TA_JUSTIFY, leading=15, spaceBefore=14, spaceAfter=8)

    # Menu pages
    add("SectionHeader",
        fontName="Times-Bold", fontSize=15, textColor=PRIMARY,
        alignment=TA_LEFT, spaceBefore=10, spaceAfter=2)
    add("SubcatHeader",
        fontName="Times-Bold", fontSize=12, textColor=PRIMARY,
        alignment=TA_LEFT, spaceBefore=8, spaceAfter=2)
    add("DishName",
        fontName="Times-Bold", fontSize=11, textColor=TEXT_COLOR,
        alignment=TA_RIGHT, spaceAfter=1)
    add("DishDesc",
        fontName="Times-Italic", fontSize=9, textColor=GREY,
        alignment=TA_RIGHT, leading=12, spaceAfter=6)

    return s


# ── Running header / footer ───────────────────────────────────────────────────
def _draw_header(canv, doc):
    """Small logo left, company name + tagline right, gold rule below."""
    canv.saveState()

    logo_h = 22 * mm
    logo_y = PH - TM + 8 * mm

    if os.path.exists(LOGO_PATH):
        try:
            canv.drawImage(
                LOGO_PATH,
                LM, logo_y,
                width=logo_h, height=logo_h,
                preserveAspectRatio=True, mask="auto",
            )
        except Exception:
            pass

    # Company name
    canv.setFont("Times-Bold", 12)
    canv.setFillColor(PRIMARY)
    canv.drawRightString(PW - RM, PH - TM + 22 * mm, COMPANY_NAME)

    # Tagline
    if TAGLINE:
        canv.setFont("Times-Italic", 9)
        canv.setFillColor(ACCENT)
        canv.drawRightString(PW - RM, PH - TM + 14 * mm, f'"{TAGLINE}"')

    # Gold rule at base of header
    canv.setStrokeColor(ACCENT)
    canv.setLineWidth(1.2)
    canv.line(LM, PH - TM + 4 * mm, PW - RM, PH - TM + 4 * mm)

    canv.restoreState()


def _draw_footer(canv, doc):
    """Page number centred, thin gold rule above."""
    canv.saveState()
    rule_y = BM - 4 * mm
    canv.setStrokeColor(ACCENT)
    canv.setLineWidth(0.5)
    canv.line(LM, rule_y, PW - RM, rule_y)

    canv.setFont("Helvetica", 8)
    canv.setFillColor(GREY)
    canv.drawCentredString(PW / 2, rule_y - 5 * mm, f"{COMPANY_NAME}  |  Page {doc.page}")

    canv.restoreState()


def _on_page(canv, doc):
    _draw_header(canv, doc)
    _draw_footer(canv, doc)


# ── Cover page ────────────────────────────────────────────────────────────────
def _cover(client_name, event_date, venue, event_title, tier_name, tier_info, styles):
    story = []

    # Large centred logo (header is already on this page, so keep logo prominent)
    story.append(Spacer(1, 6 * mm))
    if os.path.exists(LOGO_PATH):
        try:
            logo = Image(LOGO_PATH, width=1.6 * inch, height=1.6 * inch)
            logo.hAlign = "CENTER"
            story.append(logo)
        except Exception:
            pass

    story.append(Paragraph(COMPANY_NAME, styles["CoverCompany"]))
    if TAGLINE:
        story.append(Paragraph(f'<i>"{TAGLINE}"</i>', styles["CoverTagline"]))

    story.append(HRFlowable(
        width="50%", thickness=1.5, color=ACCENT,
        spaceBefore=2, spaceAfter=12, hAlign="CENTER",
    ))

    # Event title — underlined like sample menus
    if event_title:
        story.append(Paragraph(f"<u>{event_title}</u>", styles["EventTitle"]))
        story.append(Spacer(1, 2 * mm))

    # Client block — bold + underlined (matching sample style)
    if client_name:
        story.append(Paragraph(f"<u>Hosted by {client_name}</u>", styles["CoverDetail"]))
    if event_date:
        story.append(Paragraph(f"<u>Date: {event_date}</u>", styles["CoverDetail"]))
    if venue:
        story.append(Paragraph(f"<u>Venue: {venue}</u>", styles["CoverDetail"]))

    if SHOW_PRICE_ON_PDF and tier_info and tier_name:
        story.append(Spacer(1, 2 * mm))
        story.append(Paragraph(
            f"<u>{tier_name} Package  —  ₹{tier_info['price']} per head  "
            f"|  Min. {tier_info['mg']} guests</u>",
            styles["CoverDetail"],
        ))

    # About us paragraphs
    if ABOUT_US:
        for para in ABOUT_US.split("\n\n"):
            if para.strip():
                story.append(Paragraph(para.strip(), styles["AboutUs"]))

    story.append(PageBreak())
    return story


# ── Menu pages ────────────────────────────────────────────────────────────────
def _menu(selections, styles):
    story = []
    active = [(k, v) for k, v in selections.items() if any(v.values())]

    for idx, (section_name, subcategories) in enumerate(active):
        # Section name: LEFT, maroon, bold, uppercase + full-width gold rule
        story.append(Paragraph(section_name.upper(), styles["SectionHeader"]))
        story.append(HRFlowable(
            width=CW, thickness=1.5, color=ACCENT,
            spaceBefore=1, spaceAfter=8,
        ))

        for subcat_name, dishes in subcategories.items():
            if not dishes:
                continue

            # Keep subcategory header + its dishes together on the same page
            block = [
                Paragraph(subcat_name, styles["SubcatHeader"]),
                HRFlowable(
                    width=CW * 0.28, thickness=1, color=ACCENT,
                    spaceBefore=1, spaceAfter=5,
                ),
            ]
            for dish in dishes:
                block.append(Paragraph(dish["name"], styles["DishName"]))
                if dish.get("description"):
                    block.append(Paragraph(dish["description"], styles["DishDesc"]))

            story.append(KeepTogether(block))

        # Spacer between sections, but not after the last one (avoids blank trailing page)
        if idx < len(active) - 1:
            story.append(Spacer(1, 8 * mm))

    return story


# ── Entry point ───────────────────────────────────────────────────────────────
def generate_pdf(
    client_name,
    event_date,
    venue,
    menu_type_name,
    tier_name,
    tier_info,
    selections,
    event_title="",
    filename=None,
):
    """Generate a landscape A4 client menu PDF.

    Args:
        client_name:    str
        event_date:     str
        venue:          str
        menu_type_name: str — e.g. "SOCIAL (VEG) Gold"
        tier_name:      str — "Desire", "Wish", or "Walk"
        tier_info:      dict — {"price": 1200, "mg": 100}
        selections:     dict — {section: {subcategory: [{"name":..., "description":...}]}}
        event_title:    str — e.g. "Wedding Dinner", "Corporate Lunch" (shown on cover)
        filename:       optional output filename

    Returns:
        str — path to generated PDF
    """
    if filename is None:
        safe = client_name.replace(" ", "_").replace("/", "-") or "Menu"
        filename = f"TCI_Menu_{safe}.pdf"

    os.makedirs(OUTPUT_DIR, exist_ok=True)
    filepath = os.path.join(OUTPUT_DIR, filename)

    doc = SimpleDocTemplate(
        filepath,
        pagesize=PAGE,
        topMargin=TM,
        bottomMargin=BM,
        leftMargin=LM,
        rightMargin=RM,
    )

    styles = _build_styles()
    story = (
        _cover(client_name, event_date, venue, event_title, tier_name, tier_info, styles)
        + _menu(selections, styles)
    )

    doc.build(story, onFirstPage=_on_page, onLaterPages=_on_page)
    return filepath
