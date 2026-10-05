from pathlib import Path
import re

from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import mm
from reportlab.platypus import (
    SimpleDocTemplate,
    Paragraph,
    Spacer,
    Table,
    TableStyle,
    PageBreak,
    Preformatted,
)

BASE = Path(__file__).resolve().parent
INPUT = BASE / "01-final-report.md"
OUTPUT = BASE / "OWASP-Juice-Shop-Security-Assessment.pdf"

text = INPUT.read_text(encoding="utf-8")

styles = getSampleStyleSheet()

title_style = ParagraphStyle(
    "ReportTitle",
    parent=styles["Title"],
    fontSize=22,
    leading=28,
    alignment=TA_CENTER,
    spaceAfter=8 * mm,
)

subtitle_style = ParagraphStyle(
    "ReportSubtitle",
    parent=styles["Heading2"],
    fontSize=14,
    leading=18,
    alignment=TA_CENTER,
    spaceAfter=12 * mm,
)

h1_style = ParagraphStyle(
    "H1",
    parent=styles["Heading1"],
    fontSize=16,
    leading=20,
    spaceBefore=8 * mm,
    spaceAfter=4 * mm,
    keepWithNext=True,
)

h2_style = ParagraphStyle(
    "H2",
    parent=styles["Heading2"],
    fontSize=13,
    leading=17,
    spaceBefore=6 * mm,
    spaceAfter=3 * mm,
    keepWithNext=True,
)

h3_style = ParagraphStyle(
    "H3",
    parent=styles["Heading3"],
    fontSize=11,
    leading=14,
    spaceBefore=4 * mm,
    spaceAfter=2 * mm,
    keepWithNext=True,
)

body_style = ParagraphStyle(
    "Body",
    parent=styles["BodyText"],
    fontSize=9.5,
    leading=14,
    spaceAfter=3 * mm,
)

bullet_style = ParagraphStyle(
    "Bullet",
    parent=body_style,
    leftIndent=7 * mm,
    firstLineIndent=-4 * mm,
    spaceAfter=1.5 * mm,
)

code_style = ParagraphStyle(
    "Code",
    fontName="Courier",
    fontSize=7.5,
    leading=10,
    leftIndent=4 * mm,
    rightIndent=4 * mm,
    spaceBefore=2 * mm,
    spaceAfter=3 * mm,
)

meta_style = ParagraphStyle(
    "Meta",
    parent=body_style,
    fontSize=9,
    leading=13,
)

story = []


def escape(text):
    return (
        text.replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
    )


def inline_format(text):
    text = escape(text)

    text = re.sub(
        r"`([^`]+)`",
        r'<font name="Courier">\1</font>',
        text,
    )

    text = re.sub(
        r"\*\*([^*]+)\*\*",
        r"<b>\1</b>",
        text,
    )

    text = re.sub(
        r"\*([^*]+)\*",
        r"<i>\1</i>",
        text,
    )

    return text


def add_table(lines):
    rows = []

    for line in lines:
        if not line.strip():
            continue

        cells = [
            cell.strip()
            for cell in line.strip().strip("|").split("|")
        ]

        if all(re.fullmatch(r":?-+:?", cell) for cell in cells):
            continue

        rows.append(cells)

    if not rows:
        return

    max_cols = max(len(row) for row in rows)

    for row in rows:
        while len(row) < max_cols:
            row.append("")

    data = [
        [Paragraph(inline_format(cell), body_style) for cell in row]
        for row in rows
    ]

    table = Table(
        data,
        repeatRows=1,
        hAlign="LEFT",
        colWidths=[(170 / max_cols) * mm] * max_cols,
    )

    table.setStyle(
        TableStyle(
            [
                ("GRID", (0, 0), (-1, -1), 0.4, colors.grey),
                ("BACKGROUND", (0, 0), (-1, 0), colors.lightgrey),
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ("LEFTPADDING", (0, 0), (-1, -1), 4),
                ("RIGHTPADDING", (0, 0), (-1, -1), 4),
                ("TOPPADDING", (0, 0), (-1, -1), 4),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
            ]
        )
    )

    story.append(table)
    story.append(Spacer(1, 4 * mm))


lines = text.splitlines()
i = 0

while i < len(lines):
    line = lines[i].rstrip()

    if not line.strip():
        story.append(Spacer(1, 2 * mm))
        i += 1
        continue

    if line.startswith("```"):
        code_lines = []
        i += 1

        while i < len(lines) and not lines[i].startswith("```"):
            code_lines.append(lines[i])
            i += 1

        story.append(
            Preformatted(
                "\n".join(code_lines),
                code_style,
            )
        )

        i += 1
        continue

    if line.startswith("|"):
        table_lines = []

        while i < len(lines) and lines[i].strip().startswith("|"):
            table_lines.append(lines[i])
            i += 1

        add_table(table_lines)
        continue

    if line.startswith("# "):
        story.append(
            Paragraph(
                inline_format(line[2:]),
                title_style,
            )
        )
        i += 1
        continue

    if line.startswith("## "):
        story.append(
            Paragraph(
                inline_format(line[3:]),
                subtitle_style,
            )
        )
        i += 1
        continue

    if line.startswith("### "):
        story.append(
            Paragraph(
                inline_format(line[4:]),
                h2_style,
            )
        )
        i += 1
        continue

    if line.startswith("#### "):
        story.append(
            Paragraph(
                inline_format(line[5:]),
                h3_style,
            )
        )
        i += 1
        continue

    if line.startswith("- "):
        story.append(
            Paragraph(
                "• " + inline_format(line[2:]),
                bullet_style,
            )
        )
        i += 1
        continue

    if re.match(r"^\d+\.\s+", line):
        match = re.match(r"^(\d+)\.\s+(.*)$", line)

        if match:
            story.append(
                Paragraph(
                    f"{match.group(1)}. {inline_format(match.group(2))}",
                    bullet_style,
                )
            )

        i += 1
        continue

    if line == "---":
        story.append(Spacer(1, 5 * mm))
        i += 1
        continue

    story.append(
        Paragraph(
            inline_format(line),
            body_style,
        )
    )

    i += 1


def footer(canvas, doc):
    canvas.saveState()

    canvas.setFont("Helvetica", 8)

    canvas.drawString(
        20 * mm,
        12 * mm,
        "OWASP Juice Shop Security Assessment",
    )

    canvas.drawRightString(
        190 * mm,
        12 * mm,
        f"Page {doc.page}",
    )

    canvas.restoreState()


doc = SimpleDocTemplate(
    str(OUTPUT),
    pagesize=A4,
    rightMargin=20 * mm,
    leftMargin=20 * mm,
    topMargin=18 * mm,
    bottomMargin=18 * mm,
    title="OWASP Juice Shop Security Assessment",
    author="Security Assessment",
)

doc.build(
    story,
    onFirstPage=footer,
    onLaterPages=footer,
)

print(f"PDF created successfully:")
print(OUTPUT)