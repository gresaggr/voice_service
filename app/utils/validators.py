"""
Валидаторы для проверки данных
"""

import re
from typing import Optional
from .constants import REGEX_PATTERNS, MAX_USERNAME_LENGTH, MAX_VOICE_FILE_SIZE, BALANCE_TOP_UP_AMOUNTS


def validate_phone(phone: str) -> bool:
    """Валидация номера телефона"""
    if not phone:
        return False
    
    # Очищаем от пробелов и дефисов
    clean_phone = re.sub(r'[\s\-\(\)]', '', phone)
    return bool(re.match(REGEX_PATTERNS["phone"], clean_phone))


def validate_email(email: str) -> bool:
    """Валидация email"""
    if not email:
        return False
    return bool(re.match(REGEX_PATTERNS["email"], email))


def validate_username(username: str) -> bool:
    """Валидация имени пользователя"""
    if not username:
        return False
    
    if len(username.strip()) == 0:
        return False
    
    if len(username) > MAX_USERNAME_LENGTH:
        return False
    
    # Проверяем, что имя содержит хотя бы одну букву
    if not re.search(r'[a-zA-Zа-яёА-ЯЁ]', username):
        return False
    
    return True


def validate_balance_amount(amount: float) -> bool:
    """Валидация суммы пополнения баланса"""
    try:
        amount = float(amount)
        return amount > 0 and amount in BALANCE_TOP_UP_AMOUNTS
    except (ValueError, TypeError):
        return False


def validate_voice_file_size(file_size: int) -> bool:
    """Валидация размера голосового файла"""
    return 0 < file_size <= MAX_VOICE_FILE_SIZE


def validate_voice_duration(duration: int) -> bool:
    """Валидация длительности голосового сообщения"""
    from .constants import MAX_VOICE_DURATION
    return 0 < duration <= MAX_VOICE_DURATION


def validate_telegram_user_id(user_id: int) -> bool:
    """Валидация Telegram user ID"""
    try:
        user_id = int(user_id)
        return user_id > 0
    except (ValueError, TypeError):
        return False


def validate_payment_amount(amount: float, payment_method: str) -> tuple[bool, Optional[str]]:
    """
    Валидация суммы платежа в зависимости от метода оплаты
    
    Returns:
        tuple: (is_valid, error_message)
    """
    try:
        amount = float(amount)
    except (ValueError, TypeError):
        return False, "Некорректная сумма"
    
    if amount <= 0:
        return False, "Сумма должна быть больше нуля"
    
    if payment_method == "yoomoney":
        from .constants import MIN_YOOMONEY_AMOUNT
        if amount < MIN_YOOMONEY_AMOUNT:
            return False, f"Минимальная сумма для ЮMoney: {MIN_YOOMONEY_AMOUNT} руб."
    
    elif payment_method == "telegram_stars":
        from .constants import MIN_STARS_AMOUNT
        if amount < MIN_STARS_AMOUNT:
            return False, f"Минимальная сумма: {MIN_STARS_AMOUNT} звезд"
    
    return True, None


def validate_service_category(category: str) -> bool:
    """Валидация категории услуги"""
    from .constants import SERVICE_CATEGORIES
    return category in SERVICE_CATEGORIES


def validate_service_subcategory(category: str, subcategory: str) -> bool:
    """Валидация подкатегории услуги"""
    from .constants import SERVICE_SUBCATEGORIES
    
    if category not in SERVICE_SUBCATEGORIES:
        return False
    
    return subcategory in SERVICE_SUBCATEGORIES[category]


def sanitize_input(text: str, max_length: int = 1000) -> str:
    """Очистка пользовательского ввода"""
    if not text:
        return ""
    
    # Удаляем лишние пробелы
    text = re.sub(r'\s+', ' ', text.strip())
    
    # Ограничиваем длину
    if len(text) > max_length:
        text = text[:max_length]
    
    # Удаляем потенциально опасные символы
    text = re.sub(r'[<>"\']', '', text)
    
    return text


def validate_callback_data(data: str) -> bool:
    """Валидация callback data"""
    if not data:
        return False
    
    # Проверяем длину (ограничение Telegram API)
    if len(data.encode('utf-8')) > 64:
        return False
    
    # Проверяем, что нет запрещенных символов
    forbidden_chars = ['\n', '\r', '\t']
    return not any(char in data for char in forbidden_chars)


def validate_stars_amount(amount: int) -> bool:
    """Валидация количества Telegram Stars"""
    try:
        amount = int(amount)
        from .constants import MIN_STARS_AMOUNT
        return amount >= MIN_STARS_AMOUNT
    except (ValueError, TypeError):
        return False