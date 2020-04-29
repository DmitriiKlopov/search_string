from typing import Optional

from .base import BaseModel


class Error(BaseModel):
    detail: Optional[str] = None
