"""
Диалог пополнения баланса
"""

from typing import Any

from aiogram import F
from aiogram.types import Message, CallbackQuery, LabeledPrice, PreCheckoutQuery
from aiogram_dialog import Dialog, DialogManager, Window
from aiogram_dialog.widgets.text import Const, Format
from aiogram_dialog.widgets.kbd import Button, Back, Cancel, Group, Select
from aiogram_dialog.widgets.input import MessageInput

from ...states.payment import PaymentStates
from ...utils import (
    BALANCE_TOP_UP_AMOUNTS,
    PAYMENT_METHODS,
    format_currency,
    convert_rubles_to_stars,
    validate_balance_amount,
    generate_payment_id,
    MESSAGES
)


async def get_top_up_amounts(**kwargs):
    """Получение вариантов пополнения"""
    amounts = []
    for amount in BALANCE_TOP_UP_AMOUNTS:
        amounts.append({
            "amount": amount,
            "formatted": format_currency(amount),
            "stars": convert_rubles_to_stars(amount)
        })
    
    return {"amounts": amounts}


async def get_payment_methods(**kwargs):
    """Получение методов оплаты"""
    dialog_manager: DialogManager = kwargs["dialog_manager"]
    selected_amount = dialog_manager.dialog_data.get("selected_amount", 0)
    
    methods = [
        {
            "id": "yoomoney",
            "name": "💳 ЮMoney",
            "description": f"Пополнить на {format_currency(selected_amount)}"
        },
        {
            "id": "telegram_stars",
            "name": "⭐ Telegram Stars",
            "description": f"Пополнить на {convert_rubles_to_stars(selected_amount)} звезд"
        }
    ]
    
    return {
        "methods": methods,
        "amount": format_currency(selected_amount)
    }


async def amount_selected(
    callback: CallbackQuery,
    select,
    dialog_manager: DialogManager,
    item_id: str
):
    """Обработчик выбора суммы"""
    try:
        amount = float(item_id)
        if validate_balance_amount(amount):
            dialog_manager.dialog_data["selected_amount"] = amount
            await dialog_manager.next()
        else:
            await callback.message.answer("❌ Некорректная сумма")
    except ValueError:
        await callback.message.answer("❌ Ошибка при выборе суммы")


async def payment_method_selected(
    callback: CallbackQuery,
    select,
    dialog_manager: DialogManager,
    item_id: str
):
    """Обработчик выбора метода оплаты"""
    dialog_manager.dialog_data["payment_method"] = item_id
    
    if item_id == "yoomoney":
        await dialog_manager.switch_to(PaymentStates.yoomoney_payment)
    elif item_id == "telegram_stars":
        await dialog_manager.switch_to(PaymentStates.stars_payment)


async def process_yoomoney_payment(
    callback: CallbackQuery,
    button,
    dialog_manager: DialogManager,
):
    """Обработка оплаты через ЮMoney"""
    from ...services.payment_service import PaymentService
    
    payment_service = PaymentService()
    amount = dialog_manager.dialog_data["selected_amount"]
    user_id = callback.from_user.id
    
    try:
        # Создаем платеж в ЮMoney
        payment_url = await payment_service.create_yoomoney_payment(
            user_telegram_id=user_id,
            amount=amount
        )
        
        if payment_url:
            # Создаем инлайн-кнопку для перехода к оплате
            from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
            
            keyboard = InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text="💳 Перейти к оплате", url=payment_url)],
                [InlineKeyboardButton(text="✅ Я оплатил", callback_data="payment_check")]
            ])
            
            await callback.message.edit_text(
                f"💳 Пополнение баланса через ЮMoney\n\n"
                f"💰 Сумма: {format_currency(amount)}\n\n"
                f"Нажмите кнопку ниже для перехода к оплате:",
                reply_markup=keyboard
            )
            
            await dialog_manager.done()
        else:
            await callback.message.answer("❌ Ошибка при создании платежа")
    
    except Exception as e:
        await callback.message.answer("❌ Ошибка при создании платежа")
        print(f"YooMoney payment error: {e}")


async def process_stars_payment(
    callback: CallbackQuery,
    button,
    dialog_manager: DialogManager,
):
    """Обработка оплаты через Telegram Stars"""
    from ...services.payment_service import PaymentService
    
    payment_service = PaymentService()
    amount_rub = dialog_manager.dialog_data["selected_amount"]
    amount_stars = convert_rubles_to_stars(amount_rub)
    user_id = callback.from_user.id
    
    try:
        # Создаем инвойс для Telegram Stars
        payment_id = generate_payment_id()
        
        # Сохраняем информацию о платеже
        await payment_service.create_stars_payment(
            user_telegram_id=user_id,
            amount_rub=amount_rub,
            amount_stars=amount_stars,
            payment_id=payment_id
        )
        
        # Создаем инвойс
        from aiogram.types import LabeledPrice
        
        prices = [LabeledPrice(label="Пополнение баланса", amount=amount_stars)]
        
        await callback.bot.send_invoice(
            chat_id=callback.message.chat.id,
            title="Пополнение баланса",
            description=f"Пополнение баланса на {format_currency(amount_rub)}",
            payload=payment_id,
            provider_token="",  # Для Telegram Stars токен не нужен
            currency="XTR",  # Валюта для Telegram Stars
            prices=prices,
            start_parameter="balance_topup"
        )
        
        await dialog_manager.done()
    
    except Exception as e:
        await callback.message.answer("❌ Ошибка при создании платежа")
        print(f"Telegram Stars payment error: {e}")


async def custom_amount_handler(
    message: Message,
    message_input,
    dialog_manager: DialogManager,
):
    """Обработчик ввода произвольной суммы"""
    try:
        amount = float(message.text)
        
        if amount <= 0:
            await message.answer("❌ Сумма должна быть больше нуля")
            return
        
        if amount < 10:
            await message.answer("❌ Минимальная сумма пополнения: 10 рублей")
            return
        
        if amount > 50000:
            await message.answer("❌ Максимальная сумма пополнения: 50,000 рублей")
            return
        
        dialog_manager.dialog_data["selected_amount"] = amount
        await dialog_manager.switch_to(PaymentStates.select_method)
    
    except ValueError:
        await message.answer("❌ Введите корректную сумму в рублях")


# Окно выбора суммы пополнения
amount_window = Window(
    Const("💰 Выберите сумму пополнения:"),
    Group(
        Select(
            Format("{item[formatted]}"),
            id="amount_select",
            item_id_getter=lambda item: str(item["amount"]),
            items="amounts",
            on_click=amount_selected,
        ),
        width=2,
    ),
    Button(
        Const("✏️ Другая сумма"),
        id="custom_amount",
        on_click=lambda c, b, m: m.switch_to(PaymentStates.custom_amount)
    ),
    Cancel(Const("❌ Отменить")),
    getter=get_top_up_amounts,
    state=PaymentStates.select_amount,
)

# Окно ввода произвольной суммы
custom_amount_window = Window(
    Const("💰 Введите сумму пополнения в рублях:\n\n"
          "Минимум: 10 руб.\n"
          "Максимум: 50,000 руб."),
    MessageInput(custom_amount_handler),
    Back(Const("⬅️ Назад")),
    Cancel(Const("❌ Отменить")),
    state=PaymentStates.custom_amount,
)

# Окно выбора метода оплаты
method_window = Window(
    Format("💳 Сумма пополнения: {amount}\n\nВыберите способ оплаты:"),
    Group(
        Select(
            Format("{item[name]}\n{item[description]}"),
            id="method_select",
            item_id_getter=lambda item: item["id"],
            items="methods",
            on_click=payment_method_selected,
        ),
        width=1,
    ),
    Back(Const("⬅️ Назад")),
    Cancel(Const("❌ Отменить")),
    getter=get_payment_methods,
    state=PaymentStates.select_method,
)

# Окно оплаты ЮMoney
yoomoney_window = Window(
    Format("💳 Пополнение через ЮMoney\n\n"
           "💰 Сумма: {amount}\n\n"
           "Нажмите кнопку для перехода к оплате:"),
    Button(
        Const("💳 Оплатить"),
        id="pay_yoomoney",
        on_click=process_yoomoney_payment,
    ),
    Back(Const("⬅️ Назад")),
    Cancel(Const("❌ Отменить")),
    getter=get_payment_methods,
    state=PaymentStates.yoomoney_payment,
)

# Окно оплаты Telegram Stars
stars_window = Window(
    Format("⭐ Пополнение через Telegram Stars\n\n"
           "💰 Сумма: {amount}\n"
           "⭐ К оплате: {methods[1][stars]} звезд\n\n"
           "Нажмите кнопку для создания счета:"),
    Button(
        Const("⭐ Создать счет"),
        id="pay_stars",
        on_click=process_stars_payment,
    ),
    Back(Const("⬅️ Назад")),
    Cancel(Const("❌ Отменить")),
    getter=get_payment_methods,
    state=PaymentStates.stars_payment,
)

# Создаем диалог
payment_dialog = Dialog(
    amount_window,
    custom_amount_window,
    method_window,
    yoomoney_window,
    stars_window,
)