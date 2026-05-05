"""
Render HTML to PDF with WeasyPrint when available.
"""

from __future__ import annotations

import os


def render_html_to_pdf_bytes(html: str) -> bytes:
    from weasyprint import HTML  # type: ignore

    return HTML(string=html, base_url=os.getcwd()).write_pdf()
