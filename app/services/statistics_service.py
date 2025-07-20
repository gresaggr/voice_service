from datetime import datetime, timedelta
from typing import Optional, Dict, Any, List
from decimal import Decimal

from sqlalchemy import select, func, and_
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.models import (
    User, VoiceRequest, BalanceTransaction, ServiceUsage
)
from app.utils.constants import RequestStatus, TransactionType


class StatisticsService:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def create_voice_request(self, user_id: int, category: str, 
                                 subcategory: str, file_path: str, 
                                 file_duration: Optional[int] = None) -> VoiceRequest:
        """Создать запись о голосовом запросе"""
        request = VoiceRequest(
            user_id=user_id,
            category=category,
            subcategory=subcategory,
            file_path=file_path,
            file_duration=file_duration,
            status=RequestStatus.PENDING,
            created_at=datetime.utcnow()
        )
        self.session.add(request)
        await self.session.commit()
        await self.session.refresh(request)
        return request

    async def update_request_status(self, request_id: int, status: RequestStatus,
                                  result_text: Optional[str] = None,
                                  processing_time: Optional[int] = None) -> bool:
        """Обновить статус запроса"""
        try:
            update_data = {
                'status': status,
                'updated_at': datetime.utcnow()
            }
            
            if result_text is not None:
                update_data['result_text'] = result_text
            
            if processing_time is not None:
                update_data['processing_time'] = processing_time

            await self.session.execute(
                select(VoiceRequest).where(VoiceRequest.id == request_id)
            )
            
            request = await self.session.get(VoiceRequest, request_id)
            if request:
                for key, value in update_data.items():
                    setattr(request, key, value)
                await self.session.commit()
                return True
            return False
        except Exception:
            await self.session.rollback()
            return False

    async def create_service_usage(self, user_id: int, category: str, 
                                 subcategory: str, cost: Decimal, 
                                 is_free: bool = False) -> ServiceUsage:
        """Создать запись об использовании услуги"""
        usage = ServiceUsage(
            user_id=user_id,
            category=category,
            subcategory=subcategory,
            cost=cost,
            is_free=is_free,
            used_at=datetime.utcnow()
        )
        self.session.add(usage)
        await self.session.commit()
        await self.session.refresh(usage)
        return usage

    async def get_user_statistics(self, user_id: int, 
                                days: int = 30) -> Dict[str, Any]:
        """Получить статистику пользователя за период"""
        start_date = datetime.utcnow() - timedelta(days=days)
        
        # Общее количество запросов
        total_requests = await self.session.execute(
            select(func.count(VoiceRequest.id))
            .where(and_(
                VoiceRequest.user_id == user_id,
                VoiceRequest.created_at >= start_date
            ))
        )
        total_requests = total_requests.scalar()

        # Успешные запросы
        successful_requests = await self.session.execute(
            select(func.count(VoiceRequest.id))
            .where(and_(
                VoiceRequest.user_id == user_id,
                VoiceRequest.status == RequestStatus.COMPLETED,
                VoiceRequest.created_at >= start_date
            ))
        )
        successful_requests = successful_requests.scalar()

        # Общая потраченная сумма
        total_spent = await self.session.execute(
            select(func.sum(ServiceUsage.cost))
            .where(and_(
                ServiceUsage.user_id == user_id,
                ServiceUsage.used_at >= start_date,
                ServiceUsage.is_free == False
            ))
        )
        total_spent = total_spent.scalar() or Decimal('0.00')

        # Количество бесплатных использований
        free_usages = await self.session.execute(
            select(func.count(ServiceUsage.id))
            .where(and_(
                ServiceUsage.user_id == user_id,
                ServiceUsage.is_free == True,
                ServiceUsage.used_at >= start_date
            ))
        )
        free_usages = free_usages.scalar()

        # Статистика по категориям
        category_stats = await self.session.execute(
            select(
                ServiceUsage.category,
                func.count(ServiceUsage.id).label('count'),
                func.sum(ServiceUsage.cost).label('total_cost')
            )
            .where(and_(
                ServiceUsage.user_id == user_id,
                ServiceUsage.used_at >= start_date
            ))
            .group_by(ServiceUsage.category)
        )
        category_stats = [
            {
                'category': row.category,
                'count': row.count,
                'total_cost': row.total_cost or Decimal('0.00')
            }
            for row in category_stats.fetchall()
        ]

        # Общий баланс пополнений
        total_deposits = await self.session.execute(
            select(func.sum(BalanceTransaction.amount))
            .where(and_(
                BalanceTransaction.user_id == user_id,
                BalanceTransaction.transaction_type == TransactionType.CREDIT,
                BalanceTransaction.created_at >= start_date
            ))
        )
        total_deposits = total_deposits.scalar() or Decimal('0.00')

        return {
            'period_days': days,
            'total_requests': total_requests,
            'successful_requests': successful_requests,
            'success_rate': (successful_requests / total_requests * 100) if total_requests > 0 else 0,
            'total_spent': total_spent,
            'total_deposits': total_deposits,
            'free_usages': free_usages,
            'category_stats': category_stats
        }

    async def get_global_statistics(self, days: int = 7) -> Dict[str, Any]:
        """Получить общую статистику сервиса"""
        start_date = datetime.utcnow() - timedelta(days=days)

        # Общее количество пользователей
        total_users = await self.session.execute(
            select(func.count(User.id))
        )
        total_users = total_users.scalar()

        # Активные пользователи за период
        active_users = await self.session.execute(
            select(func.count(func.distinct(VoiceRequest.user_id)))
            .where(VoiceRequest.created_at >= start_date)
        )
        active_users = active_users.scalar()

        # Общее количество запросов за период
        total_requests = await self.session.execute(
            select(func.count(VoiceRequest.id))
            .where(VoiceRequest.created_at >= start_date)
        )
        total_requests = total_requests.scalar()

        # Общий доход за период
        total_revenue = await self.session.execute(
            select(func.sum(BalanceTransaction.amount))
            .where(and_(
                BalanceTransaction.transaction_type == TransactionType.CREDIT,
                BalanceTransaction.created_at >= start_date
            ))
        )
        total_revenue = total_revenue.scalar() or Decimal('0.00')

        # Топ категории
        top_categories = await self.session.execute(
            select(
                ServiceUsage.category,
                func.count(ServiceUsage.id).label('usage_count')
            )
            .where(ServiceUsage.used_at >= start_date)
            .group_by(ServiceUsage.category)
            .order_by(func.count(ServiceUsage.id).desc())
            .limit(5)
        )
        top_categories = [
            {'category': row.category, 'count': row.usage_count}
            for row in top_categories.fetchall()
        ]

        return {
            'period_days': days,
            'total_users': total_users,
            'active_users': active_users,
            'total_requests': total_requests,
            'total_revenue': total_revenue,
            'top_categories': top_categories
        }

    async def get_user_recent_requests(self, user_id: int, limit: int = 10) -> List[VoiceRequest]:
        """Получить последние запросы пользователя"""
        result = await self.session.execute(
            select(VoiceRequest)
            .where(VoiceRequest.user_id == user_id)
            .order_by(VoiceRequest.created_at.desc())
            .limit(limit)
        )
        return result.scalars().all()