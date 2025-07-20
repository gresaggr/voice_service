from aiogram import Router, F
from aiogram.types import CallbackQuery, Message
from aiogram.fsm.context import FSMContext
from decimal import Decimal
from datetime import datetime, timedelta
import logging

from app.bot.keyboards.inline import (
    get_service_categories_keyboard,
    get_service_subcategories_keyboard,
    get_main_menu_keyboard,
    get_service_confirmation_keyboard
)
from app.bot.states.service import ServiceStates
from app.database.models import ServiceCategory, ServiceSubcategory
from app.services.user_service import UserService
from app.services.voice_service import VoiceService
from app.services.balance_service import BalanceService
from app.database.engine import db_manager
from app.tasks.voice_processing import process_voice_message
from app.config import settings

service_router = Router()
logger = logging.getLogger(__name__)


@service_router.callback_query(F.data == "service_start")
async def service_start_handler(callback: CallbackQuery, state: FSMContext):
    """Start service usage."""

    service_text = (
        "🎯 <b>Выбор категории обработки</b>\n\n"
        "Выберите категорию для обработки вашего голосового сообщения:"
    )

    await callback.message.edit_text(
        service_text,
        reply_markup=get_service_categories_keyboard()
    )
    await state.set_state(ServiceStates.selecting_main_category)
    await callback.answer()


@service_router.callback_query(F.data.startswith("category_"))
async def category_selected_handler(callback: CallbackQuery, state: FSMContext):
    """Handle category selection."""

    category_value = callback.data.split("_", 1)[1]
    category = ServiceCategory(category_value)

    await state.update_data(category=category)

    voice_service = VoiceService(None)
    category_desc = voice_service.get_category_description(category)

    subcategory_text = (
        f"🎨 <b>Категория:</b> {category_desc}\n\n"
        "Выберите подкатегорию для более точной обработки:"
    )

    await callback.message.edit_text(
        subcategory_text,
        reply_markup=get_service_subcategories_keyboard(category)
    )
    await state.set_state(ServiceStates.selecting_subcategory)
    await callback.answer()


@service_router.callback_query(F.data.startswith("subcategory_"))
async def subcategory_selected_handler(callback: CallbackQuery, state: FSMContext, user: any):
    """Handle subcategory selection."""

    subcategory_value = callback.data.split("_", 1)[1]
    subcategory = ServiceSubcategory(subcategory_value)

    await state.update_data(subcategory=subcategory)

    # Check if user can use the service
    async with db_manager.get_session() as session:
        user_service = UserService(session)
        can_use_free = await user_service.can_use_free_service(user)
        time_until_free = await user_service.get_time_until_free_usage(user)

        voice_service = VoiceService(session)
        subcategory_desc = voice_service.get_subcategory_description(subcategory)

    service_cost = Decimal(str(settings.service_cost))

    if user.balance >= service_cost:
        # User can pay
        cost_text = (
            f"🎯 <b>Подкатегория:</b> {subcategory_desc}\n\n"
            f"💰 <b>Стоимость:</b> {service_cost} ₽\n"
            f"💳 <b>Ваш баланс:</b> {user.balance} ₽\n\n"
            "📤 Пришлите голосовое сообщение для обработки\n"
            f"⏱ Максимальная длительность: {settings.max_voice_duration} сек."
        )
    elif can_use_free:
        # User can use free service
        cost_text = (
            f"🎯 <b>Подкатегория:</b> {subcategory_desc}\n\n"
            f"🎁 <b>Бесплатное использование</b>\n"
            f"💳 <b>Ваш баланс:</b> {user.balance} ₽\n\n"
            "📤 Пришлите голосовое сообщение для обработки\n"
            f"⏱ Максимальная длительность: {settings.max_voice_duration} сек.\n\n"
            f"ℹ️ Следующее бесплатное использование будет доступно через {settings.free_usage_hours} часов"
        )
    else:
        # User cannot use service
        hours_left = int(time_until_free.total_seconds() // 3600) + 1
        minutes_left = int((time_until_free.total_seconds() % 3600) // 60)

        if hours_left > 0:
            time_text = f"{hours_left} ч. {minutes_left} мин."
        else:
            time_text = f"{minutes_left} мин."

        cost_text = (
            f"🎯 <b>Подкатегория:</b> {subcategory_desc}\n\n"
            f"❌ <b>Недостаточно средств</b>\n"
            f"💰 <b>Стоимость:</b> {service_cost} ₽\n"
            f"💳 <b>Ваш баланс:</b> {user.balance} ₽\n\n"
            f"⏰ До бесплатного использования осталось: <b>{time_text}</b>\n\n"
            "💎 Пополните баланс для мгновенного доступа"
        )

        await callback.message.edit_text(
            cost_text,
            reply_markup=get_main_menu_keyboard()
        )
        await state.clear()
        await callback.answer()
        return

    await callback.message.edit_text(
        cost_text,
        reply_markup=get_service_confirmation_keyboard()
    )
    await state.set_state(ServiceStates.waiting_voice)
    await callback.answer()


@service_router.callback_query(F.data == "service_confirm")
async def service_confirm_handler(callback: CallbackQuery, state: FSMContext):
    """Confirm service usage."""

    confirm_text = (
        "🎙 <b>Отправьте голосовое сообщение</b>\n\n"
        f"⏱ Максимальная длительность: {settings.max_voice_duration} сек.\n"
        f"📁 Поддерживаемые форматы: {', '.join(settings.supported_formats)}\n"
        f"📏 Максимальный размер: {settings.max_file_size // (1024 * 1024)} МБ\n\n"
        "💡 Для лучшего результата говорите четко и медленно"
    )

    await callback.message.edit_text(
        confirm_text,
        reply_markup=None
    )
    await callback.answer()


@service_router.callback_query(F.data == "service_cancel")
async def service_cancel_handler(callback: CallbackQuery, state: FSMContext):
    """Cancel service usage."""

    await callback.message.edit_text(
        "❌ <b>Использование услуги отменено</b>\n\n"
        "Возвращайтесь когда будете готовы! 😊",
        reply_markup=get_main_menu_keyboard()
    )
    await state.clear()
    await callback.answer()


@service_router.message(ServiceStates.waiting_for_voice_message, F.voice)
async def voice_message_handler(message: Message, state: FSMContext, user: any):
    """Handle voice message."""

    try:
        # Get state data
        data = await state.get_data()
        category = data.get('category')
        subcategory = data.get('subcategory')

        if not category or not subcategory:
            await message.answer(
                "❌ Произошла ошибка. Попробуйте начать заново.",
                reply_markup=get_main_menu_keyboard()
            )
            await state.clear()
            return

        # Check voice duration
        if message.voice.duration > settings.max_voice_duration:
            await message.answer(
                f"❌ <b>Голосовое сообщение слишком длинное</b>\n\n"
                f"Максимальная длительность: {settings.max_voice_duration} сек.\n"
                f"Ваше сообщение: {message.voice.duration} сек.\n\n"
                "Пожалуйста, отправьте более короткое сообщение."
            )
            return

        # Check file size
        if message.voice.file_size > settings.max_file_size:
            await message.answer(
                f"❌ <b>Файл слишком большой</b>\n\n"
                f"Максимальный размер: {settings.max_file_size // (1024 * 1024)} МБ\n"
                f"Размер вашего файла: {message.voice.file_size // (1024 * 1024)} МБ\n\n"
                "Пожалуйста, отправьте файл меньшего размера."
            )
            return

        async with db_manager.get_session() as session:
            user_service = UserService(session)
            balance_service = BalanceService(session)

            service_cost = Decimal(str(settings.service_cost))
            can_use_free = await user_service.can_use_free_service(user)

            # Check payment again
            if user.balance >= service_cost:
                # Deduct payment
                await balance_service.deduct_balance(user.id, service_cost, "Service usage")
                payment_type = "paid"
                logger.info(f"User {user.id} used paid service for {service_cost}")
            elif can_use_free:
                # Mark free usage
                await user_service.mark_free_usage(user)
                payment_type = "free"
                logger.info(f"User {user.id} used free service")
            else:
                await message.answer(
                    "❌ <b>Ошибка оплаты</b>\n\n"
                    "Недостаточно средств или превышен лимит бесплатного использования.",
                    reply_markup=get_main_menu_keyboard()
                )
                await state.clear()
                return

        # Send processing message
        processing_msg = await message.answer(
            "⏳ <b>Обрабатываем ваше сообщение...</b>\n\n"
            "🎙 Анализируем голосовое сообщение\n"
            "⚡ Это может занять до минуты\n\n"
            "Пожалуйста, подождите..."
        )

        # Start voice processing task
        task_data = {
            "user_id": user.id,
            "telegram_user_id": user.telegram_id,
            "file_id": message.voice.file_id,
            "file_unique_id": message.voice.file_unique_id,
            "duration": message.voice.duration,
            "file_size": message.voice.file_size,
            "category": category.value,
            "subcategory": subcategory.value,
            "payment_type": payment_type,
            "processing_msg_id": processing_msg.message_id,
            "chat_id": message.chat.id
        }

        # Send to queue
        await process_voice_message.kiq(**task_data)

        logger.info(f"Voice processing task queued for user {user.id}")

    except Exception as e:
        logger.error(f"Error in voice message handler: {e}", exc_info=True)
        await message.answer(
            "❌ <b>Произошла ошибка</b>\n\n"
            "Попробуйте позже или обратитесь в поддержку.",
            reply_markup=get_main_menu_keyboard()
        )
    finally:
        await state.clear()


@service_router.message(ServiceStates.waiting_for_voice_message, ~F.voice)
async def invalid_voice_handler(message: Message):
    """Handle invalid message when waiting for voice."""

    await message.answer(
        "❌ <b>Неверный тип сообщения</b>\n\n"
        "Пожалуйста, отправьте голосовое сообщение.\n\n"
        "💡 Для записи голосового сообщения нажмите и удерживайте кнопку микрофона в Telegram."
    )


@service_router.callback_query(F.data == "back_to_categories")
async def back_to_categories_handler(callback: CallbackQuery, state: FSMContext):
    """Go back to categories selection."""

    await service_start_handler(callback, state)


@service_router.callback_query(F.data == "back_to_subcategories")
async def back_to_subcategories_handler(callback: CallbackQuery, state: FSMContext):
    """Go back to subcategories selection."""

    data = await state.get_data()
    category = data.get('category')

    if not category:
        await service_start_handler(callback, state)
        return

    await category_selected_handler(callback, state)
