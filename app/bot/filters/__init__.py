"""
Фильтры для телеграм бота
"""

from .custom import (
    IsRegisteredFilter,
    IsAdminFilter,
    HasPositiveBalanceFilter,
    CanUseServiceFilter
)

__all__ = [
    "IsRegisteredFilter",
    "IsAdminFilter", 
    "HasPositiveBalanceFilter",
    "CanUseServiceFilter"
]