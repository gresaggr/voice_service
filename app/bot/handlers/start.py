from aiogram import Router, F
from aiogram.filters import Command, CommandStart
from aiogram.types import Message, CallbackQuery

from app.bot.keyboards.inline import get_main_menu_keyboard
from app.services.user_service import UserService

start_router = Router()


@start_router.message(CommandStart())
async def start_handler(message: Message, user: any = None, user_service: UserService = None):
    """Handler for /start command."""
    
    welcome_text = (
        f"🎉 Добро пожаловать в сервис обработки голосовых сообщений!\n\n"
        f"👋 Привет, {message.from_user.first_name or 'пользователь'}!\n\n"
        f"🎯 Наш бот поможет обработать ваши голосовые сообщения в различных категориях:\n"
        f"• 🎨 Художественная обработка\n"
        f"• 💼 Бизнес-обработка\n" 
        f"• 🔢 Обработка цифр и данных\n\n"
        f"💰 У вас есть возможность бесплатного использования раз в сутки!\n"
        f"💳 Для неограниченного доступа пополните баланс.\n\n"
        f"Выберите действие:"
    )
    
    await message.answer(
        welcome_text,
        reply_markup=get_main_menu_keyboard()
    )


@start_router.callback_query(F.data == "back_to_main")
async def back_to_main_handler(callback: CallbackQuery):
    """Return to main menu."""
    
    main_text = (
        "🏠 Главное меню\n\n"
        "Выберите действие:"
    )
    
    await callback.message.edit_text(
        main_text,
        reply_markup=get_main_menu_keyboard()
    )
    await callback.answer()


@start_router.message(Command("help"))
async def help_handler(message: Message):
    """Handler for /help command."""
    
    help_text = (
        "ℹ️ <b>Справка по использованию бота</b>\n\n"
        
        "🎯 <b>Как использовать сервис:</b>\n"
        "1. Выберите «Использовать сервис»\n"
        "2. Выберите категорию обработки\n"
        "3. Выберите подкатегорию\n"
        "4. Отправьте голосовое сообщение\n"
        "5. Дождитесь обработки (до 1 минуты)\n"
        "6. Получите результат\n\n"
        
        "💰 <b>Система оплаты:</b>\n"
        f"• Стоимость одного запроса: {10.0} ₽\n"
        "• Бесплатное использование: 1 раз в сутки\n"
        "• Пополнение через YooMoney или Telegram Stars\n\n"
        
        "🎨 <b>Категории обработки:</b>\n"
        "• <b>Художественная:</b> диалоги, природа, музыка, поэзия\n"
        "• <b>Бизнес:</b> договоры, законы, презентации, переговоры\n"
        "• <b>Цифры:</b> маршруты, телефоны, статистика, расчёты\n\n"
        
        "📞 <b>Поддержка:</b>\n"
        "При возникновении проблем обратитесь к администратору."
    )
    
    await message.answer(help_text)


@start_router.callback_query(F.data == "help")
async def help_callback_handler(callback: CallbackQuery):
    """Help callback handler."""
    
    help_text = (
        "ℹ️ <b>Справка по использованию бота</b>\n\n"
        
        "🎯 <b>Как использовать сервис:</b>\n"
        "1. Выберите «Использовать сервис»\n"
        "2. Выберите категорию обработки\n"
        "3. Выберите подкатегорию\n"
        "4. Отправьте голосовое сообщение\n"
        "5. Дождитесь обработки (до 1 минуты)\n"
        "6. Получите результат\n\n"
        
        "💰 <b>Система оплаты:</b>\n"
        f"• Стоимость одного запроса: {10.0} ₽\n"
        "• Бесплатное использование: 1 раз в сутки\n"
        "• Пополнение через YooMoney или Telegram Stars\n\n"
        
        "🎨 <b>Категории обработки:</b>\n"
        "• <b>Художественная:</b> диалоги, природа, музыка, поэзия\n"
        "• <b>Бизнес:</b> договоры, законы, презентации, переговоры\n"
        "• <b>Цифры:</b> маршруты, телефоны, статистика, расчёты\n\n"
        
        "📞 <b>Поддержка:</b>\n"
        "При возникновении проблем обратитесь к администратору."
    )
    
    await callback.message.edit_text(help_text, reply_markup=get_main_menu_keyboard())
    await callback.answer()