#!/usr/bin/env python3
"""Build the free printable monthly budget worksheet (2-page PDF).

Run: python3 _build/make_pdf.py
Out: assets/bloom-and-budget-monthly-budget.pdf
"""

from pathlib import Path

from reportlab.lib.colors import HexColor
from reportlab.lib.pagesizes import LETTER
from reportlab.lib.units import inch
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.pdfgen import canvas

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "assets" / "bloom-and-budget-monthly-budget.pdf"

INK = HexColor("#22392b")
INK_SOFT = HexColor("#4c5f52")
MUTED = HexColor("#667568")
ROSE = HexColor("#a85a3c")
ROSE_LIGHT = HexColor("#d88c6e")
CREAM = HexColor("#faf6f0")
CREAM_DARK = HexColor("#f2ebdf")
LINE = HexColor("#d6cdbe")
SAGE = HexColor("#e7efe8")

F = "/usr/share/fonts/truetype/dejavu/"
pdfmetrics.registerFont(TTFont("Serif", F + "DejaVuSerif.ttf"))
pdfmetrics.registerFont(TTFont("SerifBold", F + "DejaVuSerif-Bold.ttf"))
pdfmetrics.registerFont(TTFont("Sans", F + "DejaVuSans.ttf"))
pdfmetrics.registerFont(TTFont("SansBold", F + "DejaVuSans-Bold.ttf"))

W, H = LETTER
M = 0.72 * inch
CONTENT = W - M * 2

SECTIONS = [
    ("INCOME", [
        "Take-home pay (after tax)",
        "Other income (side work, gifts)",
    ], "Total income"),
    ("THE FOUR WALLS", [
        "Rent / mortgage",
        "Utilities (power, water, internet)",
        "Groceries",
        "Transport (fuel, transit, parking)",
        "Minimum debt payments",
    ], "Total fixed costs"),
    ("FLEXIBLE SPENDING", [
        "Fun money",
        "Eating out and coffee",
        "Shopping and personal care",
        "Subscriptions",
        "Everything else",
    ], "Total flexible"),
    ("SAVINGS AND SINKING FUNDS", [
        "Emergency fund",
        "Sinking funds (travel, gifts, repairs)",
        "Long-term savings / retirement",
    ], "Total saved"),
]


def header(c, page, kicker, title, subtitle=None):
    c.setFillColor(ROSE)
    c.rect(0, H - 0.13 * inch, W, 0.13 * inch, stroke=0, fill=1)
    c.setFont("SansBold", 9)
    c.drawString(M, H - 0.62 * inch, kicker.upper())
    c.setFont("SerifBold", 25)
    c.setFillColor(INK)
    c.drawString(M, H - 1.02 * inch, title)
    if subtitle:
        c.setFont("Sans", 9.5)
        c.setFillColor(MUTED)
        c.drawString(M, H - 1.26 * inch, subtitle)

    # footer
    c.setStrokeColor(LINE)
    c.setLineWidth(0.6)
    c.line(M, 0.78 * inch, W - M, 0.78 * inch)
    c.setFont("Sans", 7.5)
    c.setFillColor(MUTED)
    c.drawString(M, 0.58 * inch, "Bloom & Budget  |  bloomandbudget.com  |  Free for personal use")
    c.drawRightString(W - M, 0.58 * inch, f"Page {page} of 2")


ROW_H = 18


def row(c, y, label, bold=False, shade=False):
    if shade:
        c.setFillColor(CREAM)
        c.rect(M, y - 6, CONTENT, ROW_H, stroke=0, fill=1)
    c.setFillColor(INK if bold else INK_SOFT)
    c.setFont("SansBold" if bold else "Sans", 9.5)
    c.drawString(M + 6, y, label)
    # planned / actual lines
    c.setStrokeColor(LINE)
    c.setLineWidth(0.7)
    c.line(W - M - 190, y - 2, W - M - 100, y - 2)
    c.line(W - M - 88, y - 2, W - M, y - 2)
    return y - ROW_H


def page_one(c):
    header(c, 1, "Bloom & Budget", "Monthly budget",
           "Print one per month. Fill in planned first, actual as the month goes.")

    # month / year fields
    y = H - 1.5 * inch
    c.setFont("Sans", 9.5)
    c.setFillColor(INK_SOFT)
    c.drawString(M, y, "Month:")
    c.setStrokeColor(LINE)
    c.line(M + 48, y - 2, M + 200, y - 2)
    c.drawString(M + 225, y, "Year:")
    c.line(M + 265, y - 2, M + 360, y - 2)

    y -= 34
    c.setFont("SansBold", 7.5)
    c.setFillColor(MUTED)
    c.drawRightString(W - M - 100, y, "PLANNED")
    c.drawRightString(W - M, y, "ACTUAL")
    y -= 8

    for title, rows, total in SECTIONS:
        y -= 14
        c.setStrokeColor(LINE)
        c.setLineWidth(1)
        c.line(M, y + 12, W - M, y + 12)
        c.setFont("SansBold", 9)
        c.setFillColor(ROSE)
        c.drawString(M, y, title)
        y -= 14
        for i, label in enumerate(rows):
            y = row(c, y, label, shade=(i % 2 == 1))
        y -= 2
        y = row(c, y, total, bold=True)
        y -= 4

    # summary
    y -= 2
    c.setFillColor(SAGE)
    c.roundRect(M, y - 80, CONTENT, 74, 8, stroke=0, fill=1)
    c.setFillColor(INK)
    c.setFont("SansBold", 9)
    c.drawString(M + 18, y - 20, "THE ONLY THREE NUMBERS THAT MATTER")

    c.setFont("Sans", 9.5)
    lines = [
        ("Total income", "what actually lands in your account"),
        ("Total planned spending", "fixed costs + flexible spending"),
        ("Left over", "income minus planned spending. If it is negative, cut flexible first."),
    ]
    ly = y - 38
    for label, hint in lines:
        c.setFont("SansBold", 9)
        c.setFillColor(INK)
        c.drawString(M + 18, ly, label)
        c.setFont("Sans", 8.5)
        c.setFillColor(INK_SOFT)
        c.drawString(M + 150, ly, hint)
        c.setStrokeColor(LINE)
        c.line(W - M - 110, ly - 2, W - M - 18, ly - 2)
        ly -= 17

    c.setFont("Serif", 10)
    c.setFillColor(INK_SOFT)
    c.drawString(M, y - 100, "\u201cA budget is a permission slip, not a punishment.\u201d")


def page_two(c):
    header(c, 2, "Bloom & Budget", "Ten minutes, in this order",
           "Do these once and the month mostly runs itself.")

    y = H - 1.75 * inch
    steps = [
        ("Write your take-home pay, not your salary.",
         "The number that lands in the account after tax, not the one in the offer letter."),
        ("Fill the four walls first.",
         "Rent, utilities, groceries, transport, minimum debt payments. These come before anything fun."),
        ("Choose the savings number before the spending number.",
         "A fixed transfer on payday. Decide it once, then stop deciding."),
        ("Give the rest a job.",
         "Weekly spending, one guilt-free treat, a small buffer for whatever you forgot."),
        ("Write down what actually happened.",
         "The gap between planned and actual is the whole lesson. No shame in the gap."),
    ]
    for i, (title, detail) in enumerate(steps, start=1):
        c.setStrokeColor(ROSE)
        c.setLineWidth(1.2)
        c.rect(M, y - 3, 11, 11, stroke=1, fill=0)
        c.setFillColor(INK)
        c.setFont("SansBold", 10.5)
        c.drawString(M + 22, y, f"{i}. {title}")
        c.setFillColor(INK_SOFT)
        c.setFont("Sans", 9)
        c.drawString(M + 22, y - 14, detail)
        y -= 42

    # two transfers box
    y -= 6
    c.setFillColor(CREAM)
    c.roundRect(M, y - 108, CONTENT, 104, 8, stroke=0, fill=1)
    c.setFillColor(ROSE)
    c.setFont("SansBold", 9)
    c.drawString(M + 18, y - 22, "SET UP TWO AUTOMATIC TRANSFERS")

    c.setFillColor(INK_SOFT)
    c.setFont("Sans", 9)
    c.drawString(M + 18, y - 44, "1.  Payday: a fixed amount to savings. Even $20. Small and automatic beats big and imagined.")
    c.drawString(M + 18, y - 62, "2.  Payday: your weekly spending amount to a separate card or account. Weekly, not monthly.")
    c.setFont("Serif", 9.5)
    c.setFillColor(INK)
    c.drawString(M + 18, y - 88, "Once both run on their own, budgeting stops needing willpower.")

    # one question
    y -= 132
    c.setFillColor(INK)
    c.setFont("SansBold", 9)
    c.drawString(M, y, "ONE QUESTION BEFORE YOU SPEND")
    c.setFont("SerifBold", 14)
    c.setFillColor(INK)
    c.drawString(M, y - 26, "\u201cIs this already in the plan?\u201d")
    c.setFont("Sans", 9)
    c.setFillColor(INK_SOFT)
    c.drawString(M, y - 44, "If yes, spend it happily. If no, either move money from another line or skip it. Both answers are fine.")

    # next month
    y -= 82
    c.setStrokeColor(LINE)
    c.setLineWidth(0.8)
    c.line(M, y, W - M, y)
    c.setFont("SansBold", 9)
    c.setFillColor(ROSE)
    c.drawString(M, y - 20, "KEEP GOING")
    c.setFillColor(INK_SOFT)
    c.setFont("Sans", 9)
    c.drawString(M, y - 40, "Print a fresh copy each month, or reuse one with a pencil. Track only the four walls and the")
    c.drawString(M, y - 55, "savings transfer if a full worksheet feels like too much at first. That is already most of the work.")

    c.setFillColor(MUTED)
    c.setFont("Sans", 8)
    c.drawString(M, y - 88, "Educational content only, not financial advice. No guarantees. Read the full disclaimer at")
    c.drawString(M, y - 100, "bloomandbudget.com/disclaimer. Free for personal use; please do not resell or republish.")


def main():
    OUT.parent.mkdir(parents=True, exist_ok=True)
    c = canvas.Canvas(str(OUT), pagesize=LETTER)
    c.setTitle("Bloom & Budget — Monthly Budget Worksheet")
    c.setAuthor("Emma Jane")
    c.setSubject("Printable monthly budget template")
    c.setCreator("Bloom & Budget")
    page_one(c)
    c.showPage()
    page_two(c)
    c.showPage()
    c.save()
    print("wrote", OUT, OUT.stat().st_size, "bytes")


if __name__ == "__main__":
    main()
