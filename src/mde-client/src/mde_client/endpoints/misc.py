from __future__ import annotations

from ..schemas import PUBLIC_PRODUCT_DTO_SCHEMA, PUBLIC_PRODUCT_FIX_DTO_SCHEMA
from .base import BaseResults


class PublicProductDTOResults(BaseResults):
    """Results from endpoints that return PublicProductDto records."""

    SCHEMA = PUBLIC_PRODUCT_DTO_SCHEMA


class ProductDTOResults(BaseResults):
    """Results from the /api/machines/{id}/getmissingkbs endpoint."""

    SCHEMA = PUBLIC_PRODUCT_FIX_DTO_SCHEMA
