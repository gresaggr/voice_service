"""
Константы для приложения
"""

# Импортируем енумы из моделей для обратной совместимости
from app.database.models import (
    ServiceCategory,
    ServiceSubcategory,
    PaymentMethod,
    PaymentStatus,
    RequestStatus,
    TransactionType
)

# Текстовые описания категорий
CATEGORY_DESCRIPTIONS = {
    ServiceCategory.ARTISTIC: "🎨 Художественная обработка",
    ServiceCategory.BUSINESS: "💼 Бизнес коммуникации",
    ServiceCategory.NUMBERS: "🔢 Работа с цифрами и данными"
}

# Текстовые описания подкатегорий
SUBCATEGORY_DESCRIPTIONS = {
    # Художественные
    ServiceSubcategory.DIALOGS: "🗣 Диалоги и беседы",
    ServiceSubcategory.NATURE: "🌿 Описание природы",
    ServiceSubcategory.MUSIC: "🎵 Музыкальное содержание",
    ServiceSubcategory.POETRY: "📝 Поэзия и стихи",

    # Бизнес
    ServiceSubcategory.AGREEMENTS: "📋 Договоры и соглашения",
    ServiceSubcategory.LAWS: "⚖️ Правовые вопросы",
    ServiceSubcategory.PRESENTATIONS: "📊 Презентации",
    ServiceSubcategory.NEGOTIATIONS: "🤝 Переговоры",

    # Цифры
    ServiceSubcategory.ROUTES: "🗺 Маршруты и направления",
    ServiceSubcategory.PHONE_NUMBERS: "📱 Номера телефонов",
    ServiceSubcategory.STATISTICS: "📈 Статистические данные",
    ServiceSubcategory.CALCULATIONS: "🧮 Расчеты и вычисления"
}

# Соответствие подкатегорий категориям
CATEGORY_SUBCATEGORIES = {
    ServiceCategory.ARTISTIC: [
        ServiceSubcategory.DIALOGS,
        ServiceSubcategory.NATURE,
        ServiceSubcategory.MUSIC,
        ServiceSubcategory.POETRY
    ],
    ServiceCategory.BUSINESS: [
        ServiceSubcategory.AGREEMENTS,
        ServiceSubcategory.LAWS,
        ServiceSubcategory.PRESENTATIONS,
        ServiceSubcategory.NEGOTIATIONS
    ],
    ServiceCategory.NUMBERS: [
        ServiceSubcategory.ROUTES,
        ServiceSubcategory.PHONE_NUMBERS,
        ServiceSubcategory.STATISTICS,
        ServiceSubcategory.CALCULATIONS
    ]
}

# Статусы запросов с эмодзи
REQUEST_STATUS_EMOJI = {
    RequestStatus.PENDING: "⏳",
    RequestStatus.PROCESSING: "⚡",
    RequestStatus.COMPLETED: "✅",
    RequestStatus.FAILED: "❌"
}

# Статусы платежей с эмодзи
PAYMENT_STATUS_EMOJI = {
    PaymentStatus.PENDING: "⏳",
    PaymentStatus.SUCCESS: "✅",
    PaymentStatus.FAILED: "❌",
    PaymentStatus.CANCELLED: "🚫"
}

# Методы платежей с эмодзи
PAYMENT_METHOD_EMOJI = {
    PaymentMethod.YOOMONEY: "💳",
    PaymentMethod.TELEGRAM_STARS: "⭐"
}

# Лимиты системы
MAX_VOICE_MESSAGE_DURATION = 300  # секунд
MAX_FILE_SIZE = 20 * 1024 * 1024  # 20MB в байтах
FREE_USAGE_COOLDOWN_HOURS = 24

# Сообщения об ошибках
ERROR_MESSAGES = {
    "user_not_found": "❌ Пользователь не найден",
    "insufficient_balance": "❌ Недостаточно средств на балансе",
    "voice_too_long": "❌ Голосовое сообщение слишком длинное",
    "file_too_large": "❌ Файл слишком большой",
    "unsupported_format": "❌ Неподдерживаемый формат файла",
    "processing_error": "❌ Ошибка обработки. Попробуйте позже",
    "payment_error": "❌ Ошибка при оплате",
    "rate_limit": "❌ Слишком много запросов. Подождите немного"
}

# Успешные сообщения
SUCCESS_MESSAGES = {
    "registration_complete": "✅ Регистрация завершена!",
    "payment_success": "✅ Платеж успешно обработан",
    "balance_updated": "✅ Баланс обновлен",
    "processing_started": "⏳ Обработка началась..."
}

# Форматирование времени
TIME_FORMAT = "%d.%m.%Y %H:%M"
DATE_FORMAT = "%d.%m.%Y"

# Валюта
CURRENCY = "₽"
CURRENCY_CODE = "RUB"
