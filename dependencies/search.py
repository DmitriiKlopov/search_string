from fastapi import FastAPI
from starlette.requests import Request

from ..search_string.config import SearchEngineConfig
from ..search_string.search_engine import SearchEngine


def init_search_engine(app: FastAPI, config: SearchEngineConfig):
    app.state.search_engine = SearchEngine(config)


def get_search_engine(request: Request) -> SearchEngine:
    return request.app.state.search_engine
