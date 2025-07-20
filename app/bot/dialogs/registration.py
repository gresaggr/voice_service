"""
Диалог регистрации пользователя
"""

from typing import Any

from aiogram import F
from aiogram.types import Message, CallbackQuery
from aiogram_dialog import Dialog, DialogManager, Window
from aiogram_dialog.widgets.text import Const, Format
from aiogram_dialog.widgets.input import MessageInput
from aiogram_dialog.widgets.kbd import Button, Back, Cancel

from ...states.registration import RegistrationStates
from ...utils import validate_username, sanitize_input, MESSAGES


async def username_handler(
    message: Message,
    message_input,
    dialog_manager: DialogManager,
):
    """Обработчик ввода имени пользователя"""
    username = sanitize_input(message.text, max_length=50)
    
    if not validate_username(username):
        await message.answer(
            "❌ Некорректное имя пользователя.\n"
            "Имя должно содержать от 1 до 50 символов и включать хотя бы одну букву."
        )
        return
    
    # Сохраняем имя в контекст диалога
    dialog_manager.dialog_data["username"] = username
    await dialog_manager.next()


async def phone_handler(
    message: Message,
    message_input,
    dialog_manager: DialogManager,
):
    """Обработчик ввода номера телефона"""
    from ...utils import validate_phone
    
    phone = sanitize_input(message.text)
    
    if not validate_phone(phone):
        await message.answer(
            "❌ Некорректный номер телефона.\n"
            "Пример правильного формата: +7 900 123-45-67"
        )
        return
    
    # Сохраняем телефон в контекст диалога
    dialog_manager.dialog_data["phone"] = phone
    await dialog_manager.next()


async def confirm_registration(
    callback: CallbackQuery,
    button,
    dialog_manager: DialogManager,
):
    """Подтверждение регистрации"""
    from ...services.user_service import UserService
    
    user_service = UserService()
    username = dialog_manager.dialog_data["username"]
    phone = dialog_manager.dialog_data["phone"]
    telegram_id = callback.from_user.id
    
    try:
        # Создаем пользователя
        user = await user_service.create_user(
            telegram_id=telegram_id,
            username=username,
            phone=phone
        )
        
        if user:
            await callback.message.answer(MESSAGES["registration_complete"])
            await dialog_manager.done()
        else:
            await callback.message.answer("❌ Ошибка при регистрации. Попробуйте позже.")
    
    except Exception as e:
        await callback.message.answer("❌ Ошибка при регистрации. Попробуйте позже.")
        # Логируем ошибку
        print(f"Registration error: {e}")


async def get_registration_data(**kwargs):
    """Получение данных для отображения в диалоге"""
    dialog_manager: DialogManager = kwargs["dialog_manager"]
    
    return {
        "username": dialog_manager.dialog_data.get("username", ""),
        "phone": dialog_manager.dialog_data.get("phone", ""),
    }


# Окно ввода имени
username_window = Window(
    Const("👋 Добро пожаловать!\n\n"
          "Для начала работы нужно пройти регистрацию.\n"
          "Введите ваше имя:"),
    MessageInput(username_handler),
    Cancel(Const("❌ Отменить")),
    state=RegistrationStates.enter_username,
)

# Окно ввода телефона
phone_window = Window(
    Const("📱 Теперь введите ваш номер телефона:\n\n"
          "Пример: +7 900 123-45-67"),
    MessageInput(phone_handler),
    Back(Const("⬅️ Назад")),
    Cancel(Const("❌ Отменить")),
    state=RegistrationStates.enter_phone,
)

# Окно подтверждения
confirmation_window = Window(
    Format("✅ Проверьте введенные данные:\n\n"
           "👤 Имя: {username}\n"
           "📱 Телефон: {phone}\n\n"
           "Все верно?"),
    Button(
        Const("✅ Подтвердить"),
        id="confirm",
        on_click=confirm_registration,
    ),
    Back(Const("⬅️ Исправить")),
    Cancel(Const("❌ Отменить")),
    getter=get_registration_data,
    state=RegistrationStates.confirmation,
)

# Создаем диалог
registration_dialog = Dialog(
    username_window,
    phone_window, 
    confirmation_window,
)