from aiogram import Router, F
from aiogram.types import CallbackQuery
from decimal import Decimal

from app.bot.keyboards.inline import get_balance_keyboard, get_main_menu_keyboard
from app.services.user_service import UserService
from app.services.payment_service import PaymentService
from app.database.engine import db_manager

balance_router = Router()


@balance_router.callback_query(F.data == "balance_info")
async def balance_info_handler(callback: CallbackQuery, user: any):
    """Show user balance information."""
    
    # Check free usage availability
    async with db_manager.get_session() as session:
        user_service = UserService(session)
        can_use_free = await user_service.can_use_free_service(user)
        time_until_free = await user_service.get_time_until_free_usage(user)
    
    balance_text = f"💰 <b>Ваш баланс:</b> {user.balance} ₽\n\n"
    
    if user.balance >= Decimal("10.0"):
        balance_text += "✅ У вас достаточно средств для использования сервиса!\n\n"
    else:
        balance_text += "⚠️ Недостаточно средств для платного использования.\n\n"
    
    if can_use_free:
        balance_text += "🎁 Доступно бесплатное использование!"
    elif time_until_free:
        hours = int(time_until_free.total_seconds() // 3600)
        minutes = int((time_until_free.total_seconds() % 3600) // 60)
        balance_text += f"⏰ Бесплатное использование будет доступно через: {hours}ч {minutes}м"
    
    await callback.message.edit_text(
        balance_text,
        reply_markup=get_balance_keyboard(user.balance)
    )
    await callback.answer()


@balance_router.callback_query(F.data == "payment_history")
async def payment_history_handler(callback: CallbackQuery, user: any):
    """Show user payment history."""
    
    async with db_manager.get_session() as session:
        payment_service = PaymentService(session)
        payments = await payment_service.get_user_payments(user.id, limit=10)
    
    if not payments:
        history_text = "📊 <b>История платежей</b>\n\nУ вас пока нет платежей."
    else:
        history_text = "📊 <b>История платежей</b>\n\n"
        
        for payment in payments:
            status_emoji = {
                'pending': '⏳',
                'success': '✅',
                'failed': '❌',
                'cancelled': '🚫'
            }.get(payment.status.value, '❓')
            
            method_name = {
                'yoomoney': 'YooMoney',
                'telegram_stars': 'Telegram Stars'
            }.get(payment.method.value, payment.method.value)
            
            history_text += (
                f"{status_emoji} {payment.amount} ₽ - {method_name}\n"
                f"   {payment.created_at.strftime('%d.%m.%Y %H:%M')}\n\n"
            )
    
    from app.bot.keyboards.inline import InlineKeyboardMarkup, InlineKeyboardButton
    
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🔙 К балансу", callback_data="balance_info")]
    ])
    
    await callback.message.edit_text(history_text, reply_markup=keyboard)
    await callback.answer()