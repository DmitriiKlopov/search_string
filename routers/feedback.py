from databases.core import Connection
from fastapi import APIRouter, Body, Depends
from fastapi.openapi.constants import REF_PREFIX

from ..dependencies.db import with_db_transaction
from ..models.search import FeedbackRequest


router = APIRouter()


@router.post(
    "/send_feedback",
    summary=(
        "Передача обратной связи по результатам работы пользователя "
        "с поисковой выдачей - Январь 2020"
    ),
    operation_id="send_feedback",
    response_model=FeedbackRequest,
    response_description=(
        "Принимает на вход данные поисковой строки и выбранный пользователем "
        "объект индекса"
    ),
    responses={
        400: {
            "description": "Неверные параметры запроса",
            "content": {
                "application/json": {
                    "schema": {"$ref": REF_PREFIX + "HTTPValidationError"}
                }
            },
        }
    },
)
async def send_feedback(
    body: FeedbackRequest = Body(
        ..., description="Описание выбранного пользователем элемента"
    ),
    conn: Connection = Depends(with_db_transaction)
):
    result = await conn.fetch_one(
        """
        INSERT INTO search_line.sl_feedback (
          system, 
          search_index_names_par, 
          id, 
          search_method, 
          search_string, 
          user_id
        )
        VALUES (
          :system, 
          :search_index_names_par, 
          :id, 
          :search_method, 
          :search_string, 
          :user_id
        )
        RETURNING *;
        """,
        body.dict()
    )
    return result
