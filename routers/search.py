from typing import List

from fastapi import APIRouter, Body, Depends
from fastapi.openapi.constants import REF_PREFIX

from ..dependencies.search import get_search_engine
from ..models.search import Search, SearchExtra, SearchString
from ..search_string.search_engine import SearchEngine


router = APIRouter()


@router.post(
    "",
    summary=(
        "Поиск и получение поисковых подсказок по различным блокам индекса - "
        "Реализовано"
    ),
    operation_id="search",
    response_model=List[List[SearchString]],
    response_description="Найденные поисковые подсказки",
    responses={
        400: {
            "description": "Ошибочные параметры запроса",
            "content": {
                "application/json": {
                    "schema": {"$ref": REF_PREFIX + "HTTPValidationError"}
                }
            },
        }
    },
)
def search(
    body: Search = Body(
        ..., description="Полное описание добавляемой в индекс записи"
    ),
    engine: SearchEngine = Depends(get_search_engine),
):
    """
    Принимает на вход поисковую строку, введенную пользователем,
    и выдает краткие поисковые подсказки из различных блоков поискового индекса
    """
    return engine.search(body.search_string, body.search_index_names_par)


@router.post(
    "/extra",
    summary="Получение подсказки/пояснение по записи индекса  - Реализовано",
    operation_id="extra",
    response_model=List[str],
    response_description="Подсказка/пояснение по объекту индекса",
    responses={
        400: {
            "description": "Ошибочные параметры запроса",
            "content": {
                "application/json": {
                    "schema": {"$ref": REF_PREFIX + "HTTPValidationError"}
                }
            },
        }
    },
)
def extra(
    body: SearchExtra = Body(
        ...,
        description=(
            "Описание выбранного пользователем элемента "
            "для запроса дополнительны сведений"
        ),
    ),
    engine: SearchEngine = Depends(get_search_engine),
):
    """
    Принимает на вход данные поисковой строки и выбранный пользователем объект
    индекса и возвращает дополнительное пояснение/подсказку по этому объекту
    """
    return engine.search_extra(body.search_string, body.code)
