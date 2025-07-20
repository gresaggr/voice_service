"""
Диалоги бота
"""

from .registration import registration_dialog
from .service_selection import service_selection_dialog
from .payment import payment_dialog

__all__ = [
    "registration_dialog",
    "service_selection_dialog", 
    "payment_dialog",
]