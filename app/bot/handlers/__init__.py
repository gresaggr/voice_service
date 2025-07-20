from aiogram import Dispatcher

from .start import start_router
from .registration import registration_router
from .balance import balance_router
from .service import service_router
from .payment import payment_router


def setup_handlers(dp: Dispatcher):
    """Setup all handlers."""
    dp.include_router(start_router)
    dp.include_router(registration_router)
    dp.include_router(balance_router)
    dp.include_router(service_router)
    dp.include_router(payment_router)