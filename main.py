import os
import re
import asyncio
from dotenv import load_dotenv

from aiogram import Bot, Dispatcher, F
from aiogram.types import Message, ReplyKeyboardMarkup, KeyboardButton, ReplyKeyboardRemove
from aiogram.filters import CommandStart, Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.client.session.aiohttp import AiohttpSession

from database import init_db, add_lead

# 1. Читаем ключи из .env
load_dotenv()
BOT_TOKEN = os.getenv("BOT_TOKEN")
ADMIN_ID = os.getenv("ADMIN_ID")

# 2. Подключаем SOCKS5 прокси
PROXY_URL = "socks5://127.0.0.1:10808"

session = AiohttpSession(proxy=PROXY_URL)
bot = Bot(token=BOT_TOKEN, session=session)
dp = Dispatcher()

# Шаги диалога (FSM)
class OrderForm(StatesGroup):
    name = State()
    phone = State()
    service = State()

# Клавиатуры
main_kb = ReplyKeyboardMarkup(
    keyboard=[[KeyboardButton(text="📝 Оставить заявку")]],
    resize_keyboard=True
)

cancel_kb = ReplyKeyboardMarkup(
    keyboard=[[KeyboardButton(text="❌ Отмена")]],
    resize_keyboard=True
)

# Хэндлер отмены (работает в любом состоянии)
@dp.message(F.text == "❌ Отмена")
@dp.message(Command("cancel"))
async def cancel_handler(message: Message, state: FSMContext):
    current_state = await state.get_state()
    if current_state is None:
        await message.answer("Нет активного заполнения заявки.", reply_markup=main_kb)
        return
    
    await state.clear()
    await message.answer("Действие отменено. Вы вернулись в главное меню.", reply_markup=main_kb)

@dp.message(CommandStart())
async def start_cmd(message: Message):
    await message.answer(
        f"Привет, {message.from_user.first_name}! 👋\n"
        f"Нажмите кнопку ниже, чтобы оформить заявку.",
        reply_markup=main_kb
    )

@dp.message(F.text == "📝 Оставить заявку")
async def start_form(message: Message, state: FSMContext):
    await state.set_state(OrderForm.name)
    await message.answer(
        "Как к вам обращаться? (Введите имя)",
        reply_markup=cancel_kb
    )

@dp.message(OrderForm.name)
async def process_name(message: Message, state: FSMContext):
    await state.update_data(user_name=message.text)
    await state.set_state(OrderForm.phone)
    await message.answer(
        "Укажите ваш номер телефона для связи:",
        reply_markup=cancel_kb
    )

@dp.message(OrderForm.phone)
async def process_phone(message: Message, state: FSMContext):
    raw_phone = message.text.strip()
    
    # Регулярка: проверяет формат от 10 до 15 цифр, опциональный плюс в начале
    phone_pattern = r"^\+?[0-9]{10,15}$"
    cleaned_phone = re.sub(r"[\s\-\(\)]", "", raw_phone)  # выкидываем скобки и дефисы для проверки
    
    if not re.match(phone_pattern, cleaned_phone):
        await message.answer(
            "⚠️ Пожалуйста, введите корректный номер телефона (например, +79991234567 или 89991234567):",
            reply_markup=cancel_kb
        )
        return

    await state.update_data(user_phone=cleaned_phone)
    await state.set_state(OrderForm.service)
    await message.answer(
        "Опишите вашу задачу или какую услугу хотите заказать:",
        reply_markup=cancel_kb
    )

@dp.message(OrderForm.service)
async def process_service(message: Message, state: FSMContext):
    user_data = await state.get_data()
    name = user_data["user_name"]
    phone = user_data["user_phone"]
    service = message.text

    await state.clear()
    await message.answer(
        "✅ Спасибо! Заявка успешно принята, скоро свяжемся с вами.",
        reply_markup=main_kb
    )

    # Пересылаем карточку заявки тебе в ЛС и пишем в БД
    if ADMIN_ID:
        username = f"@{message.from_user.username}" if message.from_user.username else "скрыт"
        report = (
            f"🔥 <b>Новая заявка!</b>\n\n"
            f"👤 <b>Имя:</b> {name}\n"
            f"📞 <b>Телефон:</b> {phone}\n"
            f"💬 <b>Задача:</b> {service}\n"
            f"🔗 <b>Профиль:</b> {username}"
        )
        await bot.send_message(chat_id=int(ADMIN_ID), text=report, parse_mode="HTML")
        add_lead(name=name, phone=phone, service=service, username=username)

async def main():
    init_db()
    print(">>> Бот успешно запущен и слушает Telegram...")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())