import sentry_sdk
from databases import Database
from fastapi import FastAPI
from fastapi.encoders import jsonable_encoder
from fastapi.exceptions import RequestValidationError
from sentry_sdk.integrations.asgi import SentryAsgiMiddleware
from starlette.requests import Request
from starlette.responses import JSONResponse
from starlette.status import HTTP_400_BAD_REQUEST
from starlette_prometheus import PrometheusMiddleware

from .conf import Config
from .dependencies.search import init_search_engine
from .routers import admin, feedback, search


__version__ = "1.0.1"

from .search_string.config import SearchEngineConfig


config = Config()
search_config = SearchEngineConfig()


if config.graylog.enabled:
    import logging

    from graypy import GELFRabbitHandler

    from .utils.log import AppNameFilter

    handler = GELFRabbitHandler(
        url=config.graylog.amqp_uri,
        exchange=config.graylog.amqp_exchange,
        exchange_type=config.graylog.amqp_exchange_type,
        virtual_host=config.graylog.amqp_virtual_host,
        routing_key=config.graylog.amqp_routing_key,
    )
    handler.setLevel(config.graylog.level)
    handler.addFilter(AppNameFilter(app_name="search-gw-svc"))

    root = logging.getLogger()
    root.addHandler(handler)


sentry_sdk.init()
sentry_sdk.capture_message("Sentry initialized", level="debug")

app = FastAPI(
    title="API сервиса единой поисковой строки",
    description=(
        "Описание API единой поисковой строки, "
        "позволяющей производить поиск по различным индексам"
    ),
    openapi_prefix=config.openapi_prefix,
    version=__version__,
)

# Middlewares applies in reverse order
app.add_middleware(PrometheusMiddleware)
app.add_middleware(SentryAsgiMiddleware)

# Routes
app.include_router(
    admin.router,
    prefix="",
    tags=["admins"],
    responses={404: {"description": "Not found"}},
)

app.include_router(feedback.router, tags=["Поиск по индексу"])
app.include_router(search.router, prefix="/search", tags=["Поиск по индексу"])


@app.exception_handler(RequestValidationError)
async def request_validation_exception_handler(
    request: Request, exc: RequestValidationError
) -> JSONResponse:
    return JSONResponse(
        status_code=HTTP_400_BAD_REQUEST,
        content={"detail": jsonable_encoder(exc.errors())},
    )


@app.on_event("startup")
async def startup():
    # Initialize app state

    # Set app config
    app.state.config = config

    app.state.database = Database(
        url=app.state.config.pg.dsn,
        min_size=app.state.config.pg.min_pool_size,
        max_size=app.state.config.pg.max_pool_size
    )
    await app.state.database.connect()

    init_search_engine(app, search_config)


@app.on_event("shutdown")
async def shutdown():
    await app.state.database.disconnect()
