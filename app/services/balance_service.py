from decimal import Decimal
from datetime import datetime, timedelta
from typing import Optional, Tuple
import logging

from sqlalchemy import select, update, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.models import User, BalanceTransaction, TransactionType

logger = logging.getLogger(__name__)


class BalanceService:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_user_balance(self, user_id: int) -> Decimal:
        """Получить текущий баланс пользователя по ID"""
        result = await self.session.execute(
            select(User.balance).where(User.id == user_id)
        )
        balance = result.scalar_one_or_none()
        return balance or Decimal('0.00')

    async def get_user_balance_by_telegram_id(self, telegram_id: int) -> Decimal:
        """Получить текущий баланс пользователя по Telegram ID"""
        result = await self.session.execute(
            select(User.balance).where(User.telegram_id == telegram_id)
        )
        balance = result.scalar_one_or_none()
        return balance or Decimal('0.00')

    @staticmethod
    async def can_use_service(user: User, service_cost: Decimal) -> Tuple[bool, Optional[str]]:
        """Проверить, может ли пользователь воспользоваться услугой"""
        if not user:
            return False, "Пользователь не найден"

        # Если баланс положительный и достаточный
        if user.balance >= service_cost:
            return True, None

        # Если баланс отрицательный или недостаточный, проверяем бесплатное использование
        if user.last_free_usage:
            time_since_last_free = datetime.utcnow() - user.last_free_usage.replace(tzinfo=None)
            if time_since_last_free < timedelta(hours=24):
                hours_left = 24 - time_since_last_free.total_seconds() / 3600
                return False, f"До бесплатного использования осталось {hours_left:.1f} часов"

        return True, None

    async def deduct_balance(self, user_id: int, amount: Decimal, description: str) -> bool:
        """Списать средства с баланса"""
        try:
            # Получаем пользователя для проверки
            result = await self.session.execute(
                select(User).where(User.id == user_id)
            )
            user = result.scalar_one_or_none()

            if not user:
                logger.error(f"User {user_id} not found for balance deduction")
                return False

            # Обновляем баланс пользователя
            await self.session.execute(
                update(User)
                .where(User.id == user_id)
                .values(
                    balance=User.balance - amount,
                    updated_at=datetime.utcnow()
                )
            )

            # Создаем запись о транзакции
            transaction = BalanceTransaction(
                user_id=user_id,
                amount=-amount,  # Отрицательная сумма для списания
                transaction_type=TransactionType.DEBIT,
                description=description
            )
            self.session.add(transaction)

            await self.session.commit()
            logger.info(f"Deducted {amount} from user {user_id} balance. Reason: {description}")
            return True

        except Exception as e:
            logger.error(f"Error deducting balance for user {user_id}: {e}")
            await self.session.rollback()
            return False

    async def add_balance(self, user_id: int, amount: Decimal, description: str,
                          payment_method: Optional[str] = None) -> bool:
        """Пополнить баланс пользователя"""
        try:
            # Получаем пользователя для проверки
            result = await self.session.execute(
                select(User).where(User.id == user_id)
            )
            user = result.scalar_one_or_none()

            if not user:
                logger.error(f"User {user_id} not found for balance addition")
                return False

            # Обновляем баланс пользователя
            await self.session.execute(
                update(User)
                .where(User.id == user_id)
                .values(
                    balance=User.balance + amount,
                    updated_at=datetime.utcnow()
                )
            )

            # Создаем запись о транзакции
            transaction = BalanceTransaction(
                user_id=user_id,
                amount=amount,  # Положительная сумма для пополнения
                transaction_type=TransactionType.CREDIT,
                description=description,
                payment_method=payment_method
            )
            self.session.add(transaction)

            await self.session.commit()
            logger.info(f"Added {amount} to user {user_id} balance. Reason: {description}")
            return True

        except Exception as e:
            logger.error(f"Error adding balance for user {user_id}: {e}")
            await self.session.rollback()
            return False

    async def update_last_free_usage(self, user_id: int) -> bool:
        """Обновить время последнего бесплатного использования"""
        try:
            await self.session.execute(
                update(User)
                .where(User.id == user_id)
                .values(
                    last_free_usage=datetime.utcnow(),
                    updated_at=datetime.utcnow()
                )
            )
            await self.session.commit()
            logger.info(f"Updated last free usage for user {user_id}")
            return True

        except Exception as e:
            logger.error(f"Error updating last free usage for user {user_id}: {e}")
            await self.session.rollback()
            return False

    async def get_balance_history(self, user_id: int, limit: int = 10) -> list[BalanceTransaction]:
        """Получить историю операций с балансом"""
        try:
            result = await self.session.execute(
                select(BalanceTransaction)
                .where(BalanceTransaction.user_id == user_id)
                .order_by(BalanceTransaction.created_at.desc())
                .limit(limit)
            )
            return list(result.scalars().all())

        except Exception as e:
            logger.error(f"Error getting balance history for user {user_id}: {e}")
            return []

    async def get_user_statistics(self, user_id: int) -> dict:
        """Получить статистику пользователя"""
        try:
            # Общая статистика по транзакциям
            credit_result = await self.session.execute(
                select(
                    func.sum(BalanceTransaction.amount),
                    func.count(BalanceTransaction.id)
                )
                .where(
                    BalanceTransaction.user_id == user_id,
                    BalanceTransaction.transaction_type == TransactionType.CREDIT
                )
            )
            credit_sum, credit_count = credit_result.first() or (Decimal('0.00'), 0)

            debit_result = await self.session.execute(
                select(
                    func.sum(BalanceTransaction.amount),
                    func.count(BalanceTransaction.id)
                )
                .where(
                    BalanceTransaction.user_id == user_id,
                    BalanceTransaction.transaction_type == TransactionType.DEBIT
                )
            )
            debit_sum, debit_count = debit_result.first() or (Decimal('0.00'), 0)

            # Текущий баланс
            current_balance = await self.get_user_balance(user_id)

            return {
                "current_balance": current_balance,
                "total_credited": credit_sum or Decimal('0.00'),
                "total_debited": abs(debit_sum) if debit_sum else Decimal('0.00'),
                "credit_transactions_count": credit_count,
                "debit_transactions_count": debit_count,
                "total_transactions": credit_count + debit_count
            }

        except Exception as e:
            logger.error(f"Error getting user statistics for user {user_id}: {e}")
            return {
                "current_balance": Decimal('0.00'),
                "total_credited": Decimal('0.00'),
                "total_debited": Decimal('0.00'),
                "credit_transactions_count": 0,
                "debit_transactions_count": 0,
                "total_transactions": 0
            }
