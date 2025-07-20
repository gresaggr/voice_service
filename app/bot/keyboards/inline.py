from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from decimal import Decimal

from app.database.models import ServiceCategory, ServiceSubcategory, PaymentMethod
from app.services.voice_service import VoiceService


def get_main_menu_keyboard() -> InlineKeyboardMarkup:
    """Основное меню."""
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🎯 Использовать сервис", callback_data="service_start")],
        [InlineKeyboardButton(text="💰 Мой баланс", callback_data="balance_info")],
        [InlineKeyboardButton(text="💳 Пополнить баланс", callback_data="payment_start")],
        [InlineKeyboardButton(text="📊 История запросов", callback_data="history")],
        [InlineKeyboardButton(text="ℹ️ Помощь", callback_data="help")]
    ])


def get_service_categories_keyboard() -> InlineKeyboardMarkup:
    """Клавиатура выбора категорий услуг."""
    voice_service = VoiceService(None)  # Для получения описаний
    
    buttons = []
    for category in ServiceCategory:
        description = voice_service.get_category_description(category)
        buttons.append([InlineKeyboardButton(
            text=description,
            callback_data=f"category_{category.value}"
        )])
    
    buttons.append([InlineKeyboardButton(text="🔙 Назад", callback_data="back_to_main")])
    
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def get_service_subcategories_keyboard(category: ServiceCategory) -> InlineKeyboardMarkup:
    """Клавиатура выбора подкатегорий."""
    voice_service = VoiceService(None)
    subcategories = voice_service.get_subcategories_by_category(category)
    
    buttons = []
    for subcategory in subcategories:
        description = voice_service.get_subcategory_description(subcategory)
        buttons.append([InlineKeyboardButton(
            text=description,
            callback_data=f"subcategory_{subcategory.value}"
        )])
    
    buttons.append([InlineKeyboardButton(text="🔙 К категориям", callback_data="back_to_categories")])
    
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def get_payment_amounts_keyboard() -> InlineKeyboardMarkup:
    """Клавиатура выбора сумм для пополнения."""
    amounts = [100, 300, 500, 1000, 2000]
    
    buttons = []
    for amount in amounts:
        buttons.append([InlineKeyboardButton(
            text=f"{amount} ₽",
            callback_data=f"payment_amount_{amount}"
        )])
    
    buttons.append([InlineKeyboardButton(text="💰 Другая сумма", callback_data="payment_custom_amount")])
    buttons.append([InlineKeyboardButton(text="🔙 Назад", callback_data="back_to_main")])
    
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def get_payment_methods_keyboard(amount: Decimal) -> InlineKeyboardMarkup:
    """Клавиатура выбора способов оплаты."""
    buttons = [
        [InlineKeyboardButton(
            text="💳 YooMoney",
            callback_data=f"payment_method_{PaymentMethod.YOOMONEY.value}_{amount}"
        )],
        [InlineKeyboardButton(
            text="⭐ Telegram Stars", 
            callback_data=f"payment_method_{PaymentMethod.TELEGRAM_STARS.value}_{amount}"
        )],
        [InlineKeyboardButton(text="🔙 К выбору суммы", callback_data="back_to_amounts")]
    ]
    
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def get_balance_keyboard(user_balance: Decimal) -> InlineKeyboardMarkup:
    """Клавиатура для управления балансом."""
    buttons = [
        [InlineKeyboardButton(text="💳 Пополнить баланс", callback_data="payment_start")],
        [InlineKeyboardButton(text="📊 История платежей", callback_data="payment_history")]
    ]
    
    if user_balance > 0:
        buttons.insert(0, [InlineKeyboardButton(
            text="🎯 Использовать сервис",
            callback_data="service_start"
        )])
    
    buttons.append([InlineKeyboardButton(text="🔙 Главное меню", callback_data="back_to_main")])
    
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def get_service_confirmation_keyboard() -> InlineKeyboardMarkup:
    """Клавиатура подтверждения использования сервиса."""
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="✅ Подтвердить", callback_data="service_confirm")],
        [InlineKeyboardButton(text="🔙 К подкатегориям", callback_data="back_to_subcategories")],
        [InlineKeyboardButton(text="🏠 Главное меню", callback_data="back_to_main")]
    ])


def get_back_to_categories_keyboard() -> InlineKeyboardMarkup:
    """Клавиатура возврата к категориям."""
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🔙 К категориям", callback_data="service_start")]
    ])


def get_history_keyboard() -> InlineKeyboardMarkup:
    """Клавиатура для истории запросов."""
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🔄 Обновить", callback_data="history_refresh")],
        [InlineKeyboardButton(text="🔙 Главное меню", callback_data="back_to_main")]
    ])