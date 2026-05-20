from __future__ import annotations

from .base import BaseResults
from ..schemas import PUBLIC_PRODUCT_FIX_DTO_SCHEMA


class ProductDTOResults(BaseResults):
    """Results from the /api/machines/{id}/getmissingkbs endpoint."""

    SCHEMA = PUBLIC_PRODUCT_FIX_DTO_SCHEMA
