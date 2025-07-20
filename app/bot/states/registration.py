"""
Состояния для процесса регистрации
"""
from aiogram.fsm.state import State, StatesGroup


class RegistrationStates(StatesGroup):
    """Состояния диалога регистрации"""
    
    # Ожидание имени пользователя
    waiting_for_name = State()
    
    # Ожидание email (опционально)
    waiting_for_email = State()
    
    # Ожидание согласия с условиями использования
    waiting_for_terms_agreement = State()
    
    # Подтверждение данных регистрации
    confirming_registration = State()