from decimal import Decimal
from typing import Optional, Dict, Any
import uuid
import httpx
from datetime import datetime

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.models import Payment, PaymentMethod, PaymentStatus, User
from app.config import settings


class PaymentService:
    def __init__(self, session: AsyncSession):
        self.session = session
    
    async def create_payment(
        self, 
        user_id: int, 
        amount: Decimal, 
        method: PaymentMethod
    ) -> Payment:
        """Создать новый платёж."""
        payment = Payment(
            user_id=user_id,
            amount=amount,
            method=method,
            status=PaymentStatus.PENDING
        )
        
        self.session.add(payment)
        await self.session.flush()
        await self.session.refresh(payment)
        
        # Создаём внешний платёж в зависимости от метода
        if method == PaymentMethod.YOOMONEY:
            await self.create_yoomoney_payment(payment)
        elif method == PaymentMethod.TELEGRAM_STARS:
            await self.create_telegram_stars_payment(payment)
        
        return payment
    
    @staticmethod
    async def create_yoomoney_payment(payment: Payment) -> bool:
        """Создать платёж в YooMoney."""
        if not settings.yoomoney_token:
            return False
        
        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    "https://api.yoomoney.ru/api/request-payment",
                    headers={
                        "Authorization": f"Bearer {settings.yoomoney_token}",
                        "Content-Type": "application/x-www-form-urlencoded"
                    },
                    data={
                        "pattern_id": "p2p",
                        "to": settings.yoomoney_token,  # Ваш номер кошелька
                        "amount": str(payment.amount),
                        "comment": f"Пополнение баланса #{payment.id}",
                        "message": f"Пополнение баланса в сервисе голосовых сообщений",
                        "label": str(payment.id)
                    }
                )
                
                if response.status_code == 200:
                    data = response.json()
                    payment.external_payment_id = data.get("request_id")
                    payment.payment_url = data.get("money_source", {}).get("payment_form")
                    return True
                    
        except Exception as e:
            print(f"YooMoney payment creation error: {e}")
        
        return False
    
    @staticmethod
    async def create_telegram_stars_payment(payment: Payment) -> bool:
        """Создать платёж через Telegram Stars."""
        # Здесь будет интеграция с Telegram Stars API
        # Пока что просто устанавливаем external_payment_id
        payment.external_payment_id = f"tg_stars_{payment.id}_{uuid.uuid4().hex[:8]}"
        return True
    
    async def get_payment(self, payment_id: int) -> Optional[Payment]:
        """Получить платёж по ID."""
        result = await self.session.execute(
            select(Payment).where(Payment.id == payment_id)
        )
        return result.scalar_one_or_none()
    
    async def update_payment_status(
        self, 
        payment_id: int, 
        status: PaymentStatus,
        external_payment_id: Optional[str] = None
    ) -> bool:
        """Обновить статус платежа."""
        update_data = {
            'status': status,
            'updated_at': datetime.utcnow()
        }
        
        if external_payment_id:
            update_data['external_payment_id'] = external_payment_id
        
        result = await self.session.execute(
            update(Payment)
            .where(Payment.id == payment_id)
            .values(**update_data)
        )
        
        # Если платёж успешен, пополняем баланс пользователя
        if status == PaymentStatus.SUCCESS:
            payment = await self.get_payment(payment_id)
            if payment:
                await self.session.execute(
                    update(User)
                    .where(User.id == payment.user_id)
                    .values(balance=User.balance + payment.amount)
                )
        
        return result.rowcount > 0
    
    @staticmethod
    async def check_yoomoney_payment(payment: Payment) -> PaymentStatus:
        """Проверить статус платежа в YooMoney."""
        if not settings.yoomoney_token or not payment.external_payment_id:
            return PaymentStatus.FAILED
        
        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    "https://api.yoomoney.ru/api/process-payment",
                    headers={
                        "Authorization": f"Bearer {settings.yoomoney_token}",
                        "Content-Type": "application/x-www-form-urlencoded"
                    },
                    data={
                        "request_id": payment.external_payment_id
                    }
                )
                
                if response.status_code == 200:
                    data = response.json()
                    status = data.get("status")
                    
                    if status == "success":
                        return PaymentStatus.SUCCESS
                    elif status in ["refused", "fail"]:
                        return PaymentStatus.FAILED
                        
        except Exception as e:
            print(f"YooMoney payment check error: {e}")
        
        return PaymentStatus.PENDING
    
    async def get_user_payments(
        self, 
        user_id: int, 
        limit: int = 10
    ) -> list[Payment]:
        """Получить платежи пользователя."""
        result = await self.session.execute(
            select(Payment)
            .where(Payment.user_id == user_id)
            .order_by(Payment.created_at.desc())
            .limit(limit)
        )
        return result.scalars().all()