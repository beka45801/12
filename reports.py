"""Отчёты: текст в чат и Excel-файл."""
import io
from datetime import date, datetime

from openpyxl import Workbook
from openpyxl.styles import Alignment, Font, PatternFill
from openpyxl.utils import get_column_letter

from config import CURRENCY
from database import get_tx
from utils import fmt


def _by_cat(rows, kind):
    d = {}
    for r in rows:
        if r["kind"] == kind:
            d[r["category"]] = d.get(r["category"], 0) + r["amount"]
    return sorted(d.items(), key=lambda x: -x[1])


def summary_text(user_id: int, start: date, end: date, title: str) -> str:
    """Короткий отчёт для чата."""
    rows = get_tx(user_id, start, end)
    income = sum(r["amount"] for r in rows if r["kind"] == "income")
    expense = sum(r["amount"] for r in rows if r["kind"] == "expense")

    text = f"📊 <b>{title}</b>\n{start.strftime('%d.%m.%Y')} — {end.strftime('%d.%m.%Y')}\n\n"
    text += f"💰 Доход: <b>{fmt(income)}</b> {CURRENCY}\n"
    text += f"💸 Расход: <b>{fmt(expense)}</b> {CURRENCY}\n"
    text += f"📈 Прибыль: <b>{fmt(income - expense)}</b> {CURRENCY}\n"

    exp = _by_cat(rows, "expense")
    if exp:
        text += "\n<b>Куда ушли деньги:</b>\n"
        for cat, s in exp:
            pct = s / expense * 100 if expense else 0
            text += f"• {cat}: {fmt(s)} ({pct:.0f}%)\n"

    inc = _by_cat(rows, "income")
    if inc:
        text += "\n<b>Откуда доход:</b>\n"
        for cat, s in inc:
            text += f"• {cat}: {fmt(s)}\n"

    if not rows:
        text += "\nЗаписей за этот период нет."
    return text


def build_xlsx(user_id: int, start: date, end: date) -> bytes:
    """Excel с тремя листами: Итоги, Операции, По дням."""
    rows = get_tx(user_id, start, end)
    income = sum(r["amount"] for r in rows if r["kind"] == "income")
    expense = sum(r["amount"] for r in rows if r["kind"] == "expense")

    bold = Font(bold=True)
    head_fill = PatternFill("solid", fgColor="DDEBF7")

    def style_header(ws, row, cols):
        for col in range(1, cols + 1):
            ws.cell(row, col).font = bold
            ws.cell(row, col).fill = head_fill

    wb = Workbook()

    # ---------- Лист 1: Итоги ----------
    ws = wb.active
    ws.title = "Итоги"
    ws.append([f"Отчёт {start.strftime('%d.%m.%Y')} — {end.strftime('%d.%m.%Y')}"])
    ws["A1"].font = Font(bold=True, size=14)
    ws.append([])
    ws.append(["Доход", income])
    ws.append(["Расход", expense])
    ws.append(["Прибыль", income - expense])
    for r in (3, 4, 5):
        ws.cell(r, 1).font = bold

    ws.append([])
    ws.append(["Расходы по категориям", "Сумма", "%"])
    style_header(ws, ws.max_row, 3)
    for cat, s in _by_cat(rows, "expense"):
        ws.append([cat, s, round(s / expense * 100, 1) if expense else 0])

    ws.append([])
    ws.append(["Доходы по источникам", "Сумма"])
    style_header(ws, ws.max_row, 2)
    for cat, s in _by_cat(rows, "income"):
        ws.append([cat, s])

    # ---------- Лист 2: Операции ----------
    ws2 = wb.create_sheet("Операции")
    ws2.append(["Дата", "Время", "Тип", "Категория", f"Сумма ({CURRENCY})"])
    style_header(ws2, 1, 5)
    for r in rows:
        d, t = r["created_at"].split(" ")
        ws2.append([
            datetime.strptime(d, "%Y-%m-%d").strftime("%d.%m.%Y"),
            t[:5],
            "Доход" if r["kind"] == "income" else "Расход",
            r["category"],
            r["amount"],
        ])

    # ---------- Лист 3: По дням ----------
    ws3 = wb.create_sheet("По дням")
    ws3.append(["Дата", "Доход", "Расход", "Прибыль"])
    style_header(ws3, 1, 4)
    days = {}
    for r in rows:
        x = days.setdefault(r["day"], [0, 0])
        x[0 if r["kind"] == "income" else 1] += r["amount"]
    for d in sorted(days):
        i, e = days[d]
        ws3.append([datetime.strptime(d, "%Y-%m-%d").strftime("%d.%m.%Y"), i, e, i - e])

    # Ширина колонок
    for sheet in wb.worksheets:
        for idx in range(1, sheet.max_column + 1):
            sheet.column_dimensions[get_column_letter(idx)].width = 24
            for cell in sheet[get_column_letter(idx)]:
                cell.alignment = Alignment(horizontal="left")

    buf = io.BytesIO()
    wb.save(buf)
    return buf.getvalue()
