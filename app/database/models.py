from datetime import datetime
from decimal import Decimal
from enum import Enum
from typing import Optional

from sqlalchemy import (
    BigInteger, Boolean, DateTime, Enum as SQLEnum, Numeric, String, Text,
    ForeignKey, func
)
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


class Base(DeclarativeBase):
    pass


class ServiceCategory(str, Enum):
    ARTISTIC = "artistic"
    BUSINESS = "business"
    NUMBERS = "numbers"


class ServiceSubcategory(str, Enum):
    # Artistic subcategories
    DIALOGS = "dialogs"
    NATURE = "nature"
    MUSIC = "music"
    POETRY = "poetry"

    # Business subcategories
    AGREEMENTS = "agreements"
    LAWS = "laws"
    PRESENTATIONS = "presentations"
    NEGOTIATIONS = "negotiations"

    # Numbers subcategories
    ROUTES = "routes"
    PHONE_NUMBERS = "phone_numbers"
    STATISTICS = "statistics"
    CALCULATIONS = "calculations"


class PaymentMethod(str, Enum):
    YOOMONEY = "yoomoney"
    TELEGRAM_STARS = "telegram_stars"


class PaymentStatus(str, Enum):
    PENDING = "pending"
    SUCCESS = "success"
    FAILED = "failed"
    CANCELLED = "cancelled"


class RequestStatus(str, Enum):
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"


class TransactionType(str, Enum):
    CREDIT = "credit"  # Пополнение
    DEBIT = "debit"  # Списание


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    telegram_id: Mapped[int] = mapped_column(BigInteger, unique=True, index=True)
    username: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    first_name: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    last_name: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)

    balance: Mapped[Decimal] = mapped_column(
        Numeric(precision=10, scale=2),
        default=Decimal("0.00")
    )
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    last_free_usage: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now()
    )

    # Relationships
    payments: Mapped[list["Payment"]] = relationship(back_populates="user")
    service_requests: Mapped[list["ServiceRequest"]] = relationship(back_populates="user")
    balance_transactions: Mapped[list["BalanceTransaction"]] = relationship(back_populates="user")


class Payment(Base):
    __tablename__ = "payments"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)

    amount: Mapped[Decimal] = mapped_column(Numeric(precision=10, scale=2))
    method: Mapped[PaymentMethod] = mapped_column(SQLEnum(PaymentMethod))
    status: Mapped[PaymentStatus] = mapped_column(
        SQLEnum(PaymentStatus),
        default=PaymentStatus.PENDING
    )

    external_payment_id: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    payment_url: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now()
    )

    # Relationships
    user: Mapped[User] = relationship(back_populates="payments")


class BalanceTransaction(Base):
    __tablename__ = "balance_transactions"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)

    amount: Mapped[Decimal] = mapped_column(Numeric(precision=10, scale=2))
    transaction_type: Mapped[TransactionType] = mapped_column(SQLEnum(TransactionType))
    description: Mapped[str] = mapped_column(String(500))
    payment_method: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now()
    )

    # Relationships
    user: Mapped[User] = relationship(back_populates="balance_transactions")


class ServiceRequest(Base):
    __tablename__ = "service_requests"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)

    category: Mapped[ServiceCategory] = mapped_column(SQLEnum(ServiceCategory))
    subcategory: Mapped[ServiceSubcategory] = mapped_column(SQLEnum(ServiceSubcategory))

    voice_file_id: Mapped[str] = mapped_column(String(255))
    voice_file_unique_id: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    voice_duration: Mapped[int] = mapped_column()  # Duration in seconds
    voice_file_size: Mapped[Optional[int]] = mapped_column(nullable=True)  # File size in bytes

    processed_text: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    response_text: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    status: Mapped[RequestStatus] = mapped_column(
        SQLEnum(RequestStatus),
        default=RequestStatus.PENDING
    )

    cost: Mapped[Decimal] = mapped_column(
        Numeric(precision=10, scale=2),
        default=Decimal("0.00")
    )
    is_free: Mapped[bool] = mapped_column(Boolean, default=False)

    processing_started_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True
    )
    processing_completed_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now()
    )

    # Relationships
    user: Mapped[User] = relationship(back_populates="service_requests")


class Statistics(Base):
    __tablename__ = "statistics"

    id: Mapped[int] = mapped_column(primary_key=True)

    total_users: Mapped[int] = mapped_column(default=0)
    total_requests: Mapped[int] = mapped_column(default=0)
    total_revenue: Mapped[Decimal] = mapped_column(
        Numeric(precision=12, scale=2),
        default=Decimal("0.00")
    )

    daily_users: Mapped[int] = mapped_column(default=0)
    daily_requests: Mapped[int] = mapped_column(default=0)
    daily_revenue: Mapped[Decimal] = mapped_column(
        Numeric(precision=10, scale=2),
        default=Decimal("0.00")
    )

    date: Mapped[datetime] = mapped_column(DateTime(timezone=True), index=True)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now()
    )
