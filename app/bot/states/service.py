"""
Состояния для использования сервиса обработки голосовых сообщений
"""
from aiogram.fsm.state import State, StatesGroup


class ServiceStates(StatesGroup):
    """Состояния диалога использования сервиса"""
    
    # Выбор основной категории услуги
    selecting_main_category = State()
    
    # Выбор подкатегории услуги
    selecting_subcategory = State()
    
    # Ожидание голосового сообщения от пользователя
    waiting_for_voice_message = State()
    
    # Обработка голосового сообщения (показ прогресса)
    processing_voice = State()
    
    # Показ результата обработки
    showing_result = State()
    
    # Оценка качества услуги
    rating_service = State()


class ServiceCategoryStates(StatesGroup):
    """Состояния для навигации по категориям сервиса"""
    
    # Художественная категория
    artistic_category = State()
    artistic_dialogues = State()
    artistic_nature = State()
    artistic_other = State()
    
    # Бизнес категория  
    business_category = State()
    business_agreements = State()
    business_legal = State()
    business_other = State()
    
    # Цифры/числовая категория
    numbers_category = State()
    numbers_routes = State()
    numbers_phones = State()
    numbers_other = State()