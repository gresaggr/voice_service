"""
Состояния для процесса пополнения баланса
"""
from aiogram.fsm.state import State, StatesGroup


class PaymentStates(StatesGroup):
    """Состояния диалога пополнения баланса"""
    
    # Выбор способа оплаты
    selecting_payment_method = State()
    
    # Выбор суммы пополнения
    selecting_amount = State()
    
    # Ввод кастомной суммы
    entering_custom_amount = State()
    
    # Подтверждение платежа
    confirming_payment = State()
    
    # Ожидание оплаты через YuMoney
    waiting_yumoney_payment = State()
    
    # Ожидание оплаты через Telegram Stars
    waiting_stars_payment = State()
    
    # Обработка успешного платежа
    processing_successful_payment = State()
    
    # Обработка отмененного/неудачного платежа
    processing_failed_payment = State()


class YuMoneyPaymentStates(StatesGroup):
    """Состояния для оплаты через YuMoney"""
    
    # Создание платежа
    creating_payment = State()
    
    # Ожидание подтверждения платежа
    waiting_confirmation = State()
    
    # Проверка статуса платежа
    checking_payment_status = State()


class TelegramStarsPaymentStates(StatesGroup):
    """Состояния для оплаты через Telegram Stars"""
    
    # Создание инвойса
    creating_invoice = State()
    
    # Ожидание оплаты инвойса
    waiting_invoice_payment = State()
    
    # Обработка pre-checkout запроса
    processing_pre_checkout = State()
    
    # Обработка успешной оплаты
    processing_successful_payment = State()