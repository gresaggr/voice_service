from aiogram.types import ReplyKeyboardMarkup, KeyboardButton
from aiogram.types.reply_keyboard_remove import ReplyKeyboardRemove


def get_remove_keyboard() -> ReplyKeyboardRemove:
    """Удаление клавиатуры."""
    return ReplyKeyboardRemove()


def get_main_reply_keyboard() -> ReplyKeyboardMarkup:
    """Основная reply клавиатура."""
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="🎯 Использовать сервис")],
            [KeyboardButton(text="💰 Мой баланс"), KeyboardButton(text="💳 Пополнить")],
            [KeyboardButton(text="📊 История"), KeyboardButton(text="ℹ️ Помощь")]
        ],
        resize_keyboard=True,
        one_time_keyboard=False
    )


def get_cancel_keyboard() -> ReplyKeyboardMarkup:
    """Клавиатура отмены."""
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="❌ Отмена")]
        ],
        resize_keyboard=True,
        one_time_keyboard=True
    )


def get_contact_keyboard() -> ReplyKeyboardMarkup:
    """Клавиатура для отправки контакта."""
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="📞 Поделиться контактом", request_contact=True)],
            [KeyboardButton(text="❌ Отмена")]
        ],
        resize_keyboard=True,
        one_time_keyboard=True
    )