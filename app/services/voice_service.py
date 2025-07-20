from datetime import datetime
from decimal import Decimal
from typing import Optional

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.models import (
    ServiceRequest, RequestStatus, ServiceCategory, ServiceSubcategory, User
)
from app.config import settings


class VoiceService:
    def __init__(self, session: AsyncSession):
        self.session = session
    
    async def create_service_request(
        self,
        user_id: int,
        category: ServiceCategory,
        subcategory: ServiceSubcategory,
        voice_file_id: str,
        voice_duration: int,
        is_free: bool = False
    ) -> ServiceRequest:
        """Создать запрос на обработку голосового сообщения."""
        
        cost = Decimal("0.00") if is_free else Decimal(str(settings.service_cost))
        
        service_request = ServiceRequest(
            user_id=user_id,
            category=category,
            subcategory=subcategory,
            voice_file_id=voice_file_id,
            voice_duration=voice_duration,
            cost=cost,
            is_free=is_free,
            status=RequestStatus.PENDING
        )
        
        self.session.add(service_request)
        await self.session.flush()
        await self.session.refresh(service_request)
        
        return service_request
    
    async def get_request(self, request_id: int) -> Optional[ServiceRequest]:
        """Получить запрос по ID."""
        result = await self.session.execute(
            select(ServiceRequest).where(ServiceRequest.id == request_id)
        )
        return result.scalar_one_or_none()
    
    async def update_request_status(
        self,
        request_id: int,
        status: RequestStatus,
        processed_text: Optional[str] = None,
        response_text: Optional[str] = None
    ) -> bool:
        """Обновить статус запроса."""
        
        update_data = {
            'status': status,
            'updated_at': datetime.utcnow()
        }
        
        if status == RequestStatus.PROCESSING:
            update_data['processing_started_at'] = datetime.utcnow()
        elif status in [RequestStatus.COMPLETED, RequestStatus.FAILED]:
            update_data['processing_completed_at'] = datetime.utcnow()
        
        if processed_text is not None:
            update_data['processed_text'] = processed_text
        
        if response_text is not None:
            update_data['response_text'] = response_text
        
        result = await self.session.execute(
            update(ServiceRequest)
            .where(ServiceRequest.id == request_id)
            .values(**update_data)
        )
        
        return result.rowcount > 0
    
    async def get_user_requests(
        self,
        user_id: int,
        limit: int = 10
    ) -> list[ServiceRequest]:
        """Получить запросы пользователя."""
        result = await self.session.execute(
            select(ServiceRequest)
            .where(ServiceRequest.user_id == user_id)
            .order_by(ServiceRequest.created_at.desc())
            .limit(limit)
        )
        return result.scalars().all()
    
    async def get_pending_requests(self, limit: int = 100) -> list[ServiceRequest]:
        """Получить ожидающие обработки запросы."""
        result = await self.session.execute(
            select(ServiceRequest)
            .where(ServiceRequest.status == RequestStatus.PENDING)
            .order_by(ServiceRequest.created_at.asc())
            .limit(limit)
        )
        return result.scalars().all()
    
    @staticmethod
    def get_category_description(category: ServiceCategory) -> str:
        """Получить описание категории."""
        descriptions = {
            ServiceCategory.ARTISTIC: "🎨 Художественная обработка",
            ServiceCategory.BUSINESS: "💼 Бизнес-обработка", 
            ServiceCategory.NUMBERS: "🔢 Обработка цифр и данных"
        }
        return descriptions.get(category, "Неизвестная категория")
    
    @staticmethod
    def get_subcategory_description(subcategory: ServiceSubcategory) -> str:
        """Получить описание подкатегории."""
        descriptions = {
            # Artistic
            ServiceSubcategory.DIALOGS: "💬 Диалоги и разговоры",
            ServiceSubcategory.NATURE: "🌿 Природа и окружающая среда",
            ServiceSubcategory.MUSIC: "🎵 Музыка и звуки",
            ServiceSubcategory.POETRY: "📜 Поэзия и литература",
            
            # Business
            ServiceSubcategory.AGREEMENTS: "🤝 Договоры и соглашения",
            ServiceSubcategory.LAWS: "⚖️ Законы и правила",
            ServiceSubcategory.PRESENTATIONS: "📊 Презентации и отчёты",
            ServiceSubcategory.NEGOTIATIONS: "💰 Переговоры и сделки",
            
            # Numbers
            ServiceSubcategory.ROUTES: "🗺️ Маршруты и направления",
            ServiceSubcategory.PHONE_NUMBERS: "📞 Номера телефонов",
            ServiceSubcategory.STATISTICS: "📈 Статистика и аналитика",
            ServiceSubcategory.CALCULATIONS: "🧮 Расчёты и вычисления"
        }
        return descriptions.get(subcategory, "Неизвестная подкатегория")
    
    @staticmethod
    def get_subcategories_by_category(
            category: ServiceCategory
    ) -> list[ServiceSubcategory]:
        """Получить подкатегории для категории."""
        mapping = {
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
        return mapping.get(category, [])