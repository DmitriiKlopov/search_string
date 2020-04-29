import re

from fastapi import APIRouter
from starlette.requests import Request
from starlette.responses import Response
from starlette_prometheus import metrics

from ..models.admin import Health, HeathStatus


DESCRIPTION_RE = re.compile(r"\W")

router = APIRouter()


def health(request: Request):
    h = Health(
        status=HeathStatus.PASS,
        version=request.app.version.split(".", 1)[0],
        releaseID=request.app.version,
        description=DESCRIPTION_RE.sub("-", request.app.title.lower()),
    )
    return Response(
        content=h.json(by_alias=True, skip_defaults=True),
        media_type="application/health+json",
    )


router.add_api_route("/metrics", metrics)
router.add_api_route("/health", health, response_model=Health)
