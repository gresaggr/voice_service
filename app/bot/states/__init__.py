"""
Состояния для телеграм бота и диалогов
"""

from .registration import RegistrationStates
from .service import ServiceStates
from .payment import PaymentStates

__all__ = [
    "RegistrationStates",
    "ServiceStates", 
    "PaymentStates"
]