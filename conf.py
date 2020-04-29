from __future__ import annotations

from typing import Any, Dict, Optional
from urllib.parse import urlencode

from pydantic import AnyUrl, BaseSettings, validator


try:
    from dotenv import load_dotenv
except ImportError:
    pass
else:
    load_dotenv()


def build_dsn(
    driver: str,
    host: str,
    port: int,
    db: Optional[str] = None,
    user: Optional[str] = None,
    password: Optional[str] = None,
    **params: Any,
):
    if params:
        params = urlencode(params)

    return AnyUrl.build(
        scheme=driver,
        host=host,
        port=str(port),
        path=f"/{db}",
        user=user,
        password=password,
        query=params,
    )


class BaseDBSettings(BaseSettings):
    driver: str
    host: str
    port: str
    name: Optional[str] = None
    user: Optional[str] = None
    password: Optional[str] = None
    query: Optional[Dict[str, Any]] = None
    dsn: AnyUrl = None

    @validator("dsn", allow_reuse=True)
    def build_dsn(cls, value, values):
        if value:
            return value

        query = values.get("query")
        if query is None:
            query = {}
        return build_dsn(
            driver=values["driver"],
            host=values["host"],
            port=values["port"],
            db=values.get("name"),
            user=values.get("user"),
            password=values.get("password"),
            **query,
        )


class PostgresSettings(BaseDBSettings):
    driver: str = "postgresql"
    host: str = "localhost"
    port: str = "5432"
    name: Optional[str] = "services_dev"
    user: Optional[str] = "search-line-svc"

    min_pool_size: int = 1
    max_pool_size: int = 10

    class Config:
        env_prefix = "PG_DB_"


class ElasticSettings(BaseDBSettings):
    driver: str = "http"
    host: str = "localhost"
    port: str = "9200"

    class Config:
        env_prefix = "ELASTIC_"


class GraylogSettings(BaseSettings):
    enabled: bool = False
    amqp_uri: AnyUrl = "amqp://localhost:5632"
    amqp_exchange: str = "logs.reesrtexp"
    amqp_exchange_type: str = "topic"
    amqp_virtual_host: str = "/"
    amqp_routing_key: str = None
    level: str = "INFO"

    @validator("amqp_routing_key", pre=True)
    def initialize_routing_key(cls, value, values):
        if value:
            return value
        return values.get("amqp_exchange")

    class Config:
        env_prefix = "GRAYLOG_"


class Config(BaseSettings):
    openapi_prefix: str = ""

    graylog: GraylogSettings = GraylogSettings()
    pg: PostgresSettings = PostgresSettings()
    elastic: ElasticSettings = ElasticSettings()

    class Config:
        env_prefix = "APP_"
