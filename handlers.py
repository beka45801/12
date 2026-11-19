"""Реакция бота на сообщения и нажатия кнопок."""
from aiogram import F, Router
from aiogram.filters import CommandStart
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import BufferedInputFile, CallbackQuery, Message

from config import CURRENCY, EXPENSE_CATS, INCOME_CATS
from database import add_tx, delete_last, register_user
from keyboards import (
    BTN_EXPENSE, BTN_INCOME, BTN_REPORT, BTN_UNDO,
    cats_kb, file_kb, main_kb, report_kb,
)
from reports import build_xlsx, summary_text
from utils import fmt, parse_amount, period_range

router = Router()


class Form(StatesGroup):
    """Шаги диалога при записи дохода/расхода."""
    amount = State()      # ждём сумму
    category = State()    # ждём выбор категории
    custom_cat = State()  # ждём свой текст для «Другое»


# ---------- /start ----------
@router.message(CommandStart())
async def start(m: Message, state: FSMContext):
    await state.clear()
    register_user(m.from_user.id, m.chat.id)  # запоминаем, куда слать автоотчёт
    await m.answer(
        "Привет! Я веду твой учёт денег 💵\n\n"
        "➕ Доход — записать, сколько заработал\n"
        "➖ Расход — записать трату (спрошу, на что ушло)\n"
        "📊 Отчёт — за день / неделю / месяц + Excel-файл\n\n"
        "В конце каждого месяца сам пришлю файл с отчётом.",
        reply_markup=main_kb,
    )


# ---------- Нажали «Доход» или «Расход» ----------
@router.message(F.text.in_({BTN_INCOME, BTN_EXPENSE}))
async def begin(m: Message, state: FSMContext):
    kind = "income" if m.text == BTN_INCOME else "expense"
    await state.clear()
    await state.set_state(Form.amount)
    await state.update_data(kind=kind)
    word = "доход" if kind == "income" else "расход"
    await m.answer(f"Введи сумму ({word}), в {CURRENCY}:")


# ---------- Ввели сумму ----------
@router.message(Form.amount)
async def got_amount(m: Message, state: FSMContext):
    amount = parse_amount(m.text or "")
    if amount is None:
        await m.answer("Не понял сумму. Напиши числом, например: 150000")
        return
    data = await state.get_data()
    await state.update_data(amount=amount)
    await state.set_state(Form.category)
    q = "Откуда доход?" if data["kind"] == "income" else "На что ушли деньги?"
    await m.answer(f"{fmt(amount)} {CURRENCY}. {q}", reply_markup=cats_kb(data["kind"]))


async def _save(target: Message, user_id: int, state: FSMContext, category: str):
    data = await state.get_data()
    add_tx(user_id, data["kind"], data["amount"], category)
    await state.clear()
    icon = "💰 Доход" if data["kind"] == "income" else "💸 Расход"
    await target.answer(
        f"✅ {icon} записан: {fmt(data['amount'])} {CURRENCY} — {category}",
        reply_markup=main_kb,
    )


# ---------- Выбрали категорию ----------
@router.callback_query(Form.category, F.data.startswith("cat:"))
async def got_category(cb: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    cats = INCOME_CATS if data["kind"] == "income" else EXPENSE_CATS
    cat = cats[int(cb.data.split(":")[1])]
    await cb.answer()
    if cat.endswith("Другое"):
        await state.set_state(Form.custom_cat)
        await cb.message.edit_text("Напиши своими словами, на что/откуда:")
        return
    await cb.message.edit_reply_markup(reply_markup=None)
    await _save(cb.message, cb.from_user.id, state, cat)


# ---------- Написали свою категорию ----------
@router.message(Form.custom_cat)
async def got_custom(m: Message, state: FSMContext):
    cat = (m.text or "").strip()[:60]
    if not cat:
        await m.answer("Напиши текстом.")
        return
    await _save(m, m.from_user.id, state, "➕ " + cat)


@router.callback_query(F.data == "cancel")
async def cancel(cb: CallbackQuery, state: FSMContext):
    await state.clear()
    await cb.message.edit_text("Отменено.")
    await cb.answer()


# ---------- Удалить последнюю запись ----------
@router.message(F.text == BTN_UNDO)
async def undo(m: Message, state: FSMContext):
    await state.clear()
    row = delete_last(m.from_user.id)
    if not row:
        await m.answer("Удалять нечего.")
        return
    kind = "доход" if row["kind"] == "income" else "расход"
    await m.answer(f"🗑 Удалено: {kind} {fmt(row['amount'])} {CURRENCY} ({row['category']})")


# ---------- Отчёты ----------
@router.message(F.text == BTN_REPORT)
async def report_menu(m: Message, state: FSMContext):
    await state.clear()
    await m.answer("За какой период отчёт?", reply_markup=report_kb())


@router.callback_query(F.data == "rep:menu")
async def rep_menu(cb: CallbackQuery):
    await cb.message.edit_text("За какой период отчёт?", reply_markup=report_kb())
    await cb.answer()


@router.callback_query(F.data.startswith("rep:"))
async def rep(cb: CallbackQuery):
    period = cb.data.split(":")[1]
    start_d, end_d, title = period_range(period)
    await cb.message.edit_text(
        summary_text(cb.from_user.id, start_d, end_d, title),
        reply_markup=file_kb(period),
        parse_mode="HTML",
    )
    await cb.answer()


@router.callback_query(F.data.startswith("xls:"))
async def xls(cb: CallbackQuery):
    period = cb.data.split(":")[1]
    start_d, end_d, title = period_range(period)
    data = build_xlsx(cb.from_user.id, start_d, end_d)
    name = f"report_{start_d.isoformat()}_{end_d.isoformat()}.xlsx"
    await cb.message.answer_document(BufferedInputFile(data, filename=name), caption=f"📎 {title}")
    await cb.answer()
