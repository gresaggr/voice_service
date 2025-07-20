from aiogram import Router, F
from aiogram.types import CallbackQuery, Message
from aiogram.fsm.context import FSMContext
from decimal import Decimal, InvalidOperation

from app.bot.keyboards.inline import (
    get_payment_amounts_keyboard,
    get_payment_methods_keyboard,
    get_main_menu_keyboard
)
from app.bot.states.payment import PaymentStates
from app.database.models import PaymentMethod
from app.services.payment_service import PaymentService
from app.database.engine import db_manager
from app.config import settings

payment_router = Router()


@payment_router.callback_query(F.data == "payment_start")
async def payment_start_handler(callback: CallbackQuery, state: FSMContext):
    """Start payment process."""
    
    payment_text = (
        "💳 <b>Пополнение баланса</b>\n\n"
        f"💰 Стоимость одного запроса: {settings.service_cost} ₽\n\n"
        "Выберите сумму для пополнения:"
    )
    
    await callback.message.edit_text(
        payment_text,
        reply_markup=get_payment_amounts_keyboard()
    )
    await state.set_state(PaymentStates.selecting_amount)
    await callback.answer()


@payment_router.callback_query(F.data.startswith("payment_amount_"))
async def amount_selected_handler(callback: CallbackQuery, state: FSMContext):
    """Handle amount selection."""
    
    amount_str = callback.data.split("_", 2)[2]
    amount = Decimal(amount_str)
    
    await state.update_data(amount=amount)
    
    method_text = (
        f"💳 <b>Сумма пополнения:</b> {amount} ₽\n\n"
        "Выберите способ оплаты:"
    )
    
    await callback.message.edit_text(
        method_text,
        reply_markup=get_payment_methods_keyboard(amount)
    )
    await state.set_state(PaymentStates.selecting_payment_method)
    await callback.answer()


@payment_router.callback_query(F.data == "payment_custom_amount")
async def custom_amount_handler(callback: CallbackQuery, state: FSMContext):
    """Handle custom amount input."""
    
    await callback.message.edit_text(
        "💰 <b>Ввод суммы</b>\n\n"
        "Введите желаемую сумму пополнения (от 10 до 10000 рублей):"
    )
    await state.set_state(PaymentStates.entering_custom_amount)
    await callback.answer()


@payment_router.message(PaymentStates.entering_custom_amount)
async def custom_amount_input_handler(message: Message, state: FSMContext):
    """Process custom amount input."""
    
    try:
        amount = Decimal(message.text.replace(",", "."))
        
        if amount < 10 or amount > 10000:
            await message.answer(
                "❌ Сумма должна быть от 10 до 10000 рублей.\n"
                "Попробуйте ещё раз:"
            )
            return
        
        await state.update_data(amount=amount)
        
        method_text = (
            f"💳 <b>Сумма пополнения:</b> {amount} ₽\n\n"
            "Выберите способ оплаты:"
        )
        
        await message.answer(
            method_text,
            reply_markup=get_payment_methods_keyboard(amount)
        )
        await state.set_state(PaymentStates.selecting_payment_method)
        
    except (InvalidOperation, ValueError):
        await message.answer(
            "❌ Некорректная сумма. Введите число от 10 до 10000:"
        )


@payment_router.callback_query(F.data.startswith("payment_method_"))
async def method_selected_handler(callback: CallbackQuery, state: FSMContext, user: any):
    """Handle payment method selection."""
    
    parts = callback.data.split("_")
    method = PaymentMethod(parts[2])
    amount = Decimal(parts[3])
    
    await state.update_data(method=method, amount=amount)
    
    async with db_manager.get_session() as session:
        payment_service = PaymentService(session)
        
        try:
            payment = await payment_service.create_payment(
                user_id=user.id,
                amount=amount,
                method=method
            )
            
            if method == PaymentMethod.YOOMONEY:
                # Create YooMoney payment
                payment_url = await payment_service.create_yoomoney_payment(payment)
                
                if payment_url:
                    payment_text = (
                        f"💳 <b>Оплата через YooMoney</b>\n\n"
                        f"💰 <b>Сумма:</b> {amount} ₽\n"
                        f"🆔 <b>Номер платежа:</b> #{payment.id}\n\n"
                        "Нажмите кнопку ниже для перехода к оплате:"
                    )
                    
                    from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
                    keyboard = InlineKeyboardMarkup(inline_keyboard=[
                        [InlineKeyboardButton(text="💳 Оплатить", url=payment_url)],
                        [InlineKeyboardButton(text="🔄 Проверить оплату", 
                                            callback_data=f"check_payment_{payment.id}")],
                        [InlineKeyboardButton(text="🔙 Назад", callback_data="back_to_main")]
                    ])
                else:
                    payment_text = "❌ Не удалось создать ссылку для оплаты. Попробуйте позже."
                    keyboard = get_main_menu_keyboard()
                    
            elif method == PaymentMethod.TELEGRAM_STARS:
                # Create Telegram Stars payment
                success = await payment_service.create_telegram_stars_payment(payment)
                
                if success:
                    payment_text = (
                        f"⭐ <b>Оплата через Telegram Stars</b>\n\n"
                        f"💰 <b>Сумма:</b> {amount} ⭐\n"
                        f"🆔 <b>Номер платежа:</b> #{payment.id}\n\n"
                        "Используйте встроенную систему Telegram для оплаты."
                    )
                    
                    from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
                    keyboard = InlineKeyboardMarkup(inline_keyboard=[
                        [InlineKeyboardButton(text="🔄 Проверить оплату", 
                                            callback_data=f"check_payment_{payment.id}")],
                        [InlineKeyboardButton(text="🔙 Назад", callback_data="back_to_main")]
                    ])
                else:
                    payment_text = "❌ Не удалось создать платёж. Попробуйте позже."
                    keyboard = get_main_menu_keyboard()
                    
        except Exception as e:
            payment_text = f"❌ Ошибка при создании платежа: {str(e)}"
            keyboard = get_main_menu_keyboard()
    
    await callback.message.edit_text(payment_text, reply_markup=keyboard)
    await state.clear()
    await callback.answer()


@payment_router.callback_query(F.data.startswith("check_payment_"))
async def check_payment_handler(callback: CallbackQuery, user: any):
    """Check payment status."""
    
    payment_id = int(callback.data.split("_")[2])
    
    async with db_manager.get_session() as session:
        payment_service = PaymentService(session)
        
        payment = await payment_service.get_payment(payment_id)
        if not payment or payment.user_id != user.id:
            await callback.answer("Платёж не найден", show_alert=True)
            return
        
        # Check payment status
        updated_payment = await payment_service.check_payment_status(payment)
        
        if updated_payment.status.value == "success":
            status_text = (
                f"✅ <b>Платёж успешно выполнен!</b>\n\n"
                f"💰 <b>Сумма:</b> {updated_payment.amount} ₽\n"
                f"💳 <b>Баланс пополнен на:</b> {updated_payment.amount} ₽\n\n"
                "Теперь вы можете пользоваться сервисом!"
            )
        elif updated_payment.status.value == "failed":
            status_text = (
                f"❌ <b>Платёж не выполнен</b>\n\n"
                f"Попробуйте создать новый платёж."
            )
        elif updated_payment.status.value == "cancelled":
            status_text = (
                f"🚫 <b>Платёж отменён</b>\n\n"
                f"Вы можете создать новый платёж."
            )
        else:
            status_text = (
                f"⏳ <b>Платёж ожидает оплаты</b>\n\n"
                f"Статус будет обновлён после поступления средств."
            )
    
    await callback.message.edit_text(status_text, reply_markup=get_main_menu_keyboard())
    await callback.answer()


@payment_router.callback_query(F.data == "back_to_amounts")
async def back_to_amounts_handler(callback: CallbackQuery, state: FSMContext):
    """Return to amount selection."""
    
    payment_text = (
        "💳 <b>Пополнение баланса</b>\n\n"
        f"💰 Стоимость одного запроса: {settings.service_cost} ₽\n\n"
        "Выберите сумму для пополнения:"
    )
    
    await callback.message.edit_text(
        payment_text,
        reply_markup=get_payment_amounts_keyboard()
    )
    await state.set_state(PaymentStates.selecting_amount)
    await callback.answer()