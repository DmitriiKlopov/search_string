from databases.core import Connection, Database
from fastapi import Depends
from starlette.requests import Request


def get_database(request: "Request") -> "Database":
    return request.app.state.database


async def get_db_connection(
    db: "Database" = Depends(get_database),
) -> "Connection":
    async with db.connection() as conn:
        yield conn


async def with_db_transaction(
    conn: "Connection" = Depends(get_db_connection),
) -> "Connection":
    async with conn.transaction():
        yield conn
