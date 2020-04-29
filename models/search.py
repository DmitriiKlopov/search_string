from datetime import datetime
from typing import List, Optional

from pydantic import AnyUrl, Field

from .base import BaseModel


class Search(BaseModel):
    search_string: str = Field(
        ..., description="Поисковая строка, введенная пользователем"
    )
    search_index_names_par: str = Field(
        ...,
        description=(
            "Массив названий блоков индекса, "
            "в которых должен производиться поиск. "
            'В виде строки через разделитель "|"'
        ),
    )
    limit_block: int = Field(
        5,
        ge=1,
        le=50,
        description=(
            "Максимальное количество записей, "
            "возвращаемых по каждому блоку индекса"
        ),
    )
    limit_total: int = Field(
        50,
        ge=1,
        le=200,
        description=(
            "Максимальное количество записей, "
            "возвращаемых по всем блокам индекса"
        ),
    )


class SearchExtra(BaseModel):
    search_string: str = Field(
        ..., description="Поисковая строка, введенная пользователем"
    )
    code: str = Field(
        ...,
        description=(
            "Название блока индекса, в котором должен производиться поиск"
        ),
        examle="Услуги РЭЦ, tnved | okved",
    )


class SearchString(BaseModel):
    id: str
    block: Optional[str] = None
    tags: Optional[List[str]] = None
    header: Optional[str] = None
    description: Optional[str] = Field(
        None,
        description=(
            "Краткое неиндексируемое описание объекта индекса, "
            "выводимое впоследствии в качестве пояснения к header."
        ),
    )
    url: Optional[AnyUrl] = None
    create_date: Optional[datetime] = None
    score_block: Optional[float] = Field(
        ...,
        ge=0,
        description=(
            "Значение релевантности записи нормированное в рамках блока, "
            "используемое для сортировки выдачи"
        ),
    )
    score_total: Optional[float] = Field(
        None,
        ge=0,
        description=(
            "Абслютное значение релевантности записи, "
            "используемое для сортировки выдачи"
        ),
    )

    class Config:
        schema_extra = {
            "examples": {
                "id": "d290f1ee-6c54-4b01-90e6-d701748f0851",
                "block": "tnved",
                "tags": ["Услуги РЭЦ"],
                "header": "Услуга по поддержке экспортеров",
                "description": "Закажите услугу по поддержке экспортеров",
                "url": "/services?someService",
                "create_date": "2016-08-29T09:12:33.001000+00:00",
            }
        }


class FeedbackRequest(BaseModel):
    id: str
    system: str
    search_string: str = Field(
        ..., description="Поисковая строка, введенная пользователем"
    )
    search_index_names_par: str = Field(
        ...,
        description="Название блока индекса, в котором производился поиск",
        example="Услуги РЭЦ"
    )
    search_method: str
    user_id: Optional[str] = Field(
        ..., description="Id зарегистрированного пользователя"
    )
