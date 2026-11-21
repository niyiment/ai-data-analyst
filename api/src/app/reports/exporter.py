"""Safe HTML and PDF report exporters with XSS escaping and formula neutralisation."""

import html

from app.reports.schemas import ReportResponse

_FORMULA_PREFIXES = ("=", "+", "-", "@")


def neutralize_formula(value: str) -> str:
    """Prefix leading spreadsheet formula characters to prevent formula injection."""
    if value and value[0] in _FORMULA_PREFIXES:
        return f"'{value}"
    return value


def _safe(value: str) -> str:
    return html.escape(neutralize_formula(value), quote=True)


def render_report_html(report: ReportResponse) -> str:
    """Render an escaped, self-contained HTML report."""
    sections: list[str] = []
    for item in report.items:
        sql_block = (
            f"<pre><code>{_safe(item.generated_sql)}</code></pre>" if item.generated_sql else ""
        )
        note_block = f"<p><em>{_safe(item.note)}</em></p>" if item.note else ""
        sections.append(
            f"<section><h2>{_safe(item.question)}</h2>{note_block}{sql_block}</section>"
        )

    body = "\n".join(sections) or "<p>No items in this report.</p>"
    return (
        "<!DOCTYPE html><html lang='en'><head><meta charset='utf-8'>"
        f"<title>{_safe(report.title)}</title></head>"
        f"<body><h1>{_safe(report.title)}</h1>{body}</body></html>"
    )


def _pdf_escape(text: str) -> str:
    return text.replace("\\", "\\\\").replace("(", "\\(").replace(")", "\\)")


def _pdf_lines(report: ReportResponse) -> list[str]:
    lines = [neutralize_formula(report.title), ""]
    for idx, item in enumerate(report.items, start=1):
        lines.append(f"{idx}. {neutralize_formula(item.question)}")
        if item.note:
            lines.append(f"   Note: {neutralize_formula(item.note)}")
        if item.generated_sql:
            lines.append(f"   SQL: {item.generated_sql[:90]}")
    return lines[:40]


def render_report_pdf(report: ReportResponse) -> bytes:
    """Render a minimal, valid PDF 1.4 document containing the report title and items."""
    text_ops = ["BT", "/F1 12 Tf", "50 760 Td", "16 TL"]
    text_ops.extend(f"({_pdf_escape(line)}) Tj T*" for line in _pdf_lines(report))
    text_ops.append("ET")
    stream = "\n".join(text_ops).encode("latin-1", errors="replace")

    objects = [
        b"1 0 obj << /Type /Catalog /Pages 2 0 R >> endobj\n",
        b"2 0 obj << /Type /Pages /Kids [3 0 R] /Count 1 >> endobj\n",
        (
            b"3 0 obj << /Type /Page /Parent 2 0 R /MediaBox [0 0 612 792] "
            b"/Resources << /Font << /F1 4 0 R >> >> /Contents 5 0 R >> endobj\n"
        ),
        b"4 0 obj << /Type /Font /Subtype /Type1 /BaseFont /Helvetica >> endobj\n",
        f"5 0 obj << /Length {len(stream)} >> stream\n".encode() + stream + b"\nendstream endobj\n",
    ]

    buf = bytearray(b"%PDF-1.4\n")
    offsets: list[int] = []
    for obj in objects:
        offsets.append(len(buf))
        buf.extend(obj)
    xref_pos = len(buf)
    buf.extend(f"xref\n0 {len(objects) + 1}\n0000000000 65535 f \n".encode())
    for off in offsets:
        buf.extend(f"{off:010d} 00000 n \n".encode())
    trailer = f"trailer << /Size {len(objects) + 1} /Root 1 0 R >>\nstartxref\n{xref_pos}\n%%EOF\n"
    buf.extend(trailer.encode())
    return bytes(buf)
