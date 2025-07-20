"""
Диалог выбора услуги
"""

from typing import Any

from aiogram import F
from aiogram.types import Message, CallbackQuery, Voice
from aiogram_dialog import Dialog, DialogManager, Window
from aiogram_dialog.widgets.text import Const, Format
from aiogram_dialog.widgets.input import MessageInput
from aiogram_dialog.widgets.kbd import Button, Back, Cancel, Group, Select
from aiogram_dialog.widgets.common import WhenCondition

from ...states.service import ServiceStates
from ...utils import (
    SERVICE_CATEGORIES, 
    SERVICE_SUBCATEGORIES, 
    calculate_service_price,
    format_currency,
    validate_voice_duration,
    validate_voice_file_size,
    MESSAGES
)


async def get_categories(**kwargs):
    """Получение списка категорий"""
    categories = []
    for category_id, category_name in SERVICE_CATEGORIES.items():
        categories.append({
            "id": category_id,
            "name": category_name
        })
    
    return {"categories": categories}


async def get_subcategories(**kwargs):
    """Получение списка подкатегорий"""
    dialog_manager: DialogManager = kwargs["dialog_manager"]
    selected_category = dialog_manager.dialog_data.get("selected_category")
    
    subcategories = []
    if selected_category and selected_category in SERVICE_SUBCATEGORIES:
        for subcat_id, subcat_name in SERVICE_SUBCATEGORIES[selected_category].items():
            price = calculate_service_price(selected_category, subcat_id)
            subcategories.append({
                "id": subcat_id,
                "name": subcat_name,
                "price": format_currency(price)
            })
    
    return {
        "subcategories": subcategories,
        "category_name": SERVICE_CATEGORIES.get(selected_category, "")
    }


async def category_selected(
    callback: CallbackQuery,
    select,
    dialog_manager: DialogManager,
    item_id: str
):
    """Обработчик выбора категории"""
    dialog_manager.dialog_data["selected_category"] = item_id
    await dialog_manager.next()


async def subcategory_selected(
    callback: CallbackQuery,
    select,
    dialog_manager: DialogManager,
    item_id: str
):
    """Обработчик выбора подкатегории"""
    dialog_manager.dialog_data["selected_subcategory"] = item_id
    
    # Проверяем баланс пользователя
    from ...services.user_service import UserService
    from ...services.balance_service import BalanceService
    
    user_service = UserService()
    balance_service = BalanceService()
    
    user = await user_service.get_user_by_telegram_id(callback.from_user.id)
    if not user:
        await callback.message.answer("❌ Пользователь не найден")
        return
    
    category = dialog_manager.dialog_data["selected_category"]
    price = calculate_service_price(category, item_id)
    
    # Проверяем возможность использования услуги
    can_use, error_msg = await balance_service.can_use_service(user.id, price)
    
    if not can_use:
        await callback.message.answer(f"❌ {error_msg}")
        return
    
    await dialog_manager.next()


async def voice_handler(
    message: Message,
    message_input,
    dialog_manager: DialogManager,
):
    """Обработчик голосового сообщения"""
    if not message.voice:
        await message.answer("❌ Пожалуйста, отправьте голосовое сообщение")
        return
    
    voice: Voice = message.voice
    
    # Валидация размера файла
    if not validate_voice_file_size(voice.file_size):
        await message.answer("❌ Файл слишком большой. Максимальный размер: 20 МБ")
        return
    
    # Валидация длительности
    if not validate_voice_duration(voice.duration):
        from ...utils import MAX_VOICE_DURATION
        await message.answer(f"❌ Слишком длинное сообщение. Максимум: {MAX_VOICE_DURATION} сек.")
        return
    
    # Сохраняем данные голосового сообщения
    dialog_manager.dialog_data.update({
        "voice_file_id": voice.file_id,
        "voice_duration": voice.duration,
        "voice_file_size": voice.file_size
    })
    
    await dialog_manager.next()


async def confirm_service(
    callback: CallbackQuery,
    button,
    dialog_manager: DialogManager,
):
    """Подтверждение заказа услуги"""
    from ...services.user_service import UserService
    from ...services.voice_service import VoiceService
    from ...tasks.voice_processing import process_voice_message
    
    user_service = UserService()
    voice_service = VoiceService()
    
    # Получаем пользователя
    user = await user_service.get_user_by_telegram_id(callback.from_user.id)
    if not user:
        await callback.message.answer("❌ Пользователь не найден")
        return
    
    # Получаем данные из диалога
    category = dialog_manager.dialog_data["selected_category"]
    subcategory = dialog_manager.dialog_data["selected_subcategory"]
    voice_file_id = dialog_manager.dialog_data["voice_file_id"]
    voice_duration = dialog_manager.dialog_data["voice_duration"]
    
    try:
        # Создаем запрос на обработку
        voice_request = await voice_service.create_voice_request(
            user_id=user.id,
            category=category,
            subcategory=subcategory,
            voice_file_id=voice_file_id,
            voice_duration=voice_duration
        )
        
        if voice_request:
            # Отправляем задачу в очередь
            await process_voice_message.kiq(voice_request.id)
            
            await callback.message.answer(
                f"{MESSAGES['voice_processing']}\n\n"
                f"📝 Заявка №{voice_request.id} принята в обработку"
            )
            
            await dialog_manager.done()
        else:
            await callback.message.answer("❌ Ошибка при создании запроса")
    
    except Exception as e:
        await callback.message.answer("❌ Ошибка при обработке запроса")
        print(f"Service confirmation error: {e}")


async def get_service_summary(**kwargs):
    """Получение данных для окна подтверждения"""
    dialog_manager: DialogManager = kwargs["dialog_manager"]
    
    category = dialog_manager.dialog_data.get("selected_category")
    subcategory = dialog_manager.dialog_data.get("selected_subcategory")
    voice_duration = dialog_manager.dialog_data.get("voice_duration", 0)
    
    if not category or not subcategory:
        return {}
    
    category_name = SERVICE_CATEGORIES.get(category, "")
    subcategory_name = SERVICE_SUBCATEGORIES.get(category, {}).get(subcategory, "")
    price = calculate_service_price(category, subcategory)
    
    return {
        "category_name": category_name,
        "subcategory_name": subcategory_name,
        "price": format_currency(price),
        "voice_duration": f"{voice_duration} сек."
    }


# Окно выбора категории
category_window = Window(
    Const("🎯 Выберите категорию услуги:"),
    Group(
        Select(
            Format("{item[name]}"),
            id="category_select",
            item_id_getter=lambda item: item["id"],
            items="categories",
            on_click=category_selected,
        ),
        width=1,
    ),
    Cancel(Const("❌ Отменить")),
    getter=get_categories,
    state=ServiceStates.select_category,
)

# Окно выбора подкатегории
subcategory_window = Window(
    Format("🎯 {category_name}\n\nВыберите подкатегорию:"),
    Group(
        Select(
            Format("{item[name]} - {item[price]}"),
            id="subcategory_select", 
            item_id_getter=lambda item: item["id"],
            items="subcategories",
            on_click=subcategory_selected,
        ),
        width=1,
    ),
    Back(Const("⬅️ Назад")),
    Cancel(Const("❌ Отменить")),
    getter=get_subcategories,
    state=ServiceStates.select_subcategory,
)

# Окно загрузки голосового сообщения
voice_upload_window = Window(
    Const("🎤 Отправьте голосовое сообщение для обработки:\n\n"
          "📝 Говорите четко и разборчиво\n"
          "⏱️ Максимальная длительность: 2 минуты\n"
          "📁 Максимальный размер: 20 МБ"),
    MessageInput(voice_handler, content_types=[F.voice]),
    Back(Const("⬅️ Назад")),
    Cancel(Const("❌ Отменить")),
    state=ServiceStates.upload_voice,
)

# Окно подтверждения
confirmation_window = Window(
    Format("✅ Подтверждение заказа:\n\n"
           "📂 Категория: {category_name}\n"
           "🎯 Услуга: {subcategory_name}\n"
           "💰 Стоимость: {price}\n"
           "⏱️ Длительность аудио: {voice_duration}\n\n"
           "Подтвердить заказ?"),
    Button(
        Const("✅ Подтвердить"),
        id="confirm_service",
        on_click=confirm_service,
    ),
    Back(Const("⬅️ Назад")),
    Cancel(Const("❌ Отменить")),
    getter=get_service_summary,
    state=ServiceStates.confirmation,
)

# Создаем диалог
service_selection_dialog = Dialog(
    category_window,
    subcategory_window,
    voice_upload_window,
    confirmation_window,
)