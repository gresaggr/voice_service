import asyncio
import random
from datetime import datetime

from app.tasks.broker import broker
from app.database.engine import db_manager
from app.database.models import RequestStatus, ServiceCategory, ServiceSubcategory
from app.services.voice_service import VoiceService
from app.services.user_service import UserService


@broker.task
async def process_voice_message(request_id: int, bot_token: str):
    """Задача для обработки голосового сообщения."""
    
    # Инициализируем подключение к базе данных
    if not db_manager.engine:
        db_manager.init_engine()
    
    async with db_manager.get_session() as session:
        voice_service = VoiceService(session)
        user_service = UserService(session)
        
        # Получаем запрос
        request = await voice_service.get_request(request_id)
        if not request:
            print(f"Request {request_id} not found")
            return
        
        try:
            # Помечаем запрос как обрабатываемый
            await voice_service.update_request_status(
                request_id, 
                RequestStatus.PROCESSING
            )
            
            # Имитируем загрузку и обработку файла
            # В реальном проекте здесь будет:
            # 1. Скачивание файла через Bot API
            # 2. Конвертация в нужный формат
            # 3. Распознавание речи (Speech-to-Text)
            # 4. Обработка в зависимости от категории/подкатегории
            
            # Симуляция обработки (20-60 секунд)
            processing_time = random.randint(20, 60)
            await asyncio.sleep(processing_time)
            
            # Генерируем mock результаты в зависимости от категории
            processed_text = await _mock_speech_recognition(request)
            response_text = await _mock_processing_response(
                request.category, 
                request.subcategory, 
                processed_text
            )
            
            # Обновляем запрос с результатами
            await voice_service.update_request_status(
                request_id,
                RequestStatus.COMPLETED,
                processed_text=processed_text,
                response_text=response_text
            )
            
            # Отмечаем использование бесплатной услуги, если это было бесплатно
            if request.is_free:
                await user_service.mark_free_usage(request.user_id)
            
            # Отправляем результат пользователю
            await _send_result_to_user(bot_token, request, response_text)
            
            print(f"Request {request_id} processed successfully")
            
        except Exception as e:
            print(f"Error processing request {request_id}: {e}")
            
            # Помечаем запрос как неудачный
            await voice_service.update_request_status(
                request_id,
                RequestStatus.FAILED,
                response_text=f"Ошибка обработки: {str(e)}"
            )
            
            # Возвращаем деньги, если это был платный запрос
            if not request.is_free:
                await user_service.update_balance(request.user_id, request.cost)


async def _mock_speech_recognition(request) -> str:
    """Имитация распознавания речи."""
    mock_texts = [
        "Привет, как дела? Хотел обсудить новый проект.",
        "Нужно организовать встречу на следующей неделе.",
        "Расскажи про погоду и планы на выходные.",
        "Помоги разобраться с документами и договором.",
        "Номер телефона: 8-800-123-45-67, адрес улица Ленина дом 15."
    ]
    return random.choice(mock_texts)


async def _mock_processing_response(
    category: ServiceCategory,
    subcategory: ServiceSubcategory, 
    text: str
) -> str:
    """Имитация обработки в зависимости от категории."""
    
    if category == ServiceCategory.ARTISTIC:
        if subcategory == ServiceSubcategory.DIALOGS:
            return f"🎭 Художественная интерпретация диалога:\n\n" \
                   f"Ваше сообщение преобразовано в красивый диалог:\n" \
                   f"— {text}\n— Замечательно! Давайте это обсудим подробнее."
        
        elif subcategory == ServiceSubcategory.NATURE:
            return f"🌿 Природное описание:\n\n" \
                   f"Ваши слова звучат как шёпот леса: '{text}'\n" \
                   f"Словно ветер несёт эти мысли через поля и луга..."
        
        elif subcategory == ServiceSubcategory.POETRY:
            return f"📜 Поэтическая обработка:\n\n" \
                   f"Из ваших слов родились строки:\n" \
                   f"'{text[:30]}...'\n" \
                   f"Как музыка души, что сердце трогает..."
    
    elif category == ServiceCategory.BUSINESS:
        if subcategory == ServiceSubcategory.AGREEMENTS:
            return f"🤝 Структурированное деловое предложение:\n\n" \
                   f"ПРЕДМЕТ: Обсуждение проекта\n" \
                   f"СОДЕРЖАНИЕ: {text}\n" \
                   f"СЛЕДУЮЩИЕ ШАГИ: Организация встречи и подготовка документов"
        
        elif subcategory == ServiceSubcategory.PRESENTATIONS:
            return f"📊 Структура для презентации:\n\n" \
                   f"1. Введение: {text[:50]}...\n" \
                   f"2. Основная часть: Развитие темы\n" \
                   f"3. Заключение: Выводы и предложения"
    
    elif category == ServiceCategory.NUMBERS:
        if subcategory == ServiceSubcategory.PHONE_NUMBERS:
            import re
            phones = re.findall(r'\d[\d\-\(\)\s]{7,}', text)
            if phones:
                return f"📞 Найденные контакты:\n\n" + \
                       "\n".join([f"• {phone}" for phone in phones])
            else:
                return f"📞 В сообщении не найдено номеров телефонов.\n" \
                       f"Исходный текст: {text}"
        
        elif subcategory == ServiceSubcategory.ROUTES:
            return f"🗺️ Анализ маршрута:\n\n" \
                   f"Описание: {text}\n" \
                   f"Рекомендуемый транспорт: Общественный транспорт\n" \
                   f"Примерное время: 30-45 минут"
    
    # Базовый ответ
    return f"✅ Обработка завершена.\n\n" \
           f"Исходный текст: {text}\n\n" \
           f"Категория: {category.value}\n" \
           f"Подкатегория: {subcategory.value}"


async def _send_result_to_user(bot_token: str, request, response_text: str):
    """Отправить результат пользователю через Telegram Bot API."""
    import httpx
    
    try:
        user = request.user if hasattr(request, 'user') else None
        if not user:
            # Загружаем пользователя отдельно
            async with db_manager.get_session() as session:
                user_service = UserService(session)
                user = await user_service.get_by_id(request.user_id)
        
        if user:
            async with httpx.AsyncClient() as client:
                await client.post(
                    f"https://api.telegram.org/bot{bot_token}/sendMessage",
                    json={
                        "chat_id": user.telegram_id,
                        "text": f"🎉 Ваш запрос обработан!\n\n{response_text}",
                        "parse_mode": "HTML"
                    }
                )
    except Exception as e:
        print(f"Error sending result to user: {e}")