import os
from typing import Optional

from flask import Blueprint, Response, current_app, json, jsonify, url_for


CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
with open(os.path.join(CURRENT_DIR, "openapi.json")) as f:
    openapi_spec = json.load(f)

openapi_bp = Blueprint("openapi_blueprint", __name__)


def get_swagger_ui_html(
    *,
    openapi_url: str,
    title: str,
    swagger_js_url: str = "https://cdn.jsdelivr.net/npm/swagger-ui-dist@3/swagger-ui-bundle.js",
    swagger_css_url: str = "https://cdn.jsdelivr.net/npm/swagger-ui-dist@3/swagger-ui.css",
    swagger_favicon_url: str = "https://flask.palletsprojects.com/_static/flask-icon.png",
    oauth2_redirect_url: Optional[str] = None,
    init_oauth: Optional[dict] = None,
) -> str:
    html = f"""
    <!DOCTYPE html>
    <html>
    <head>
    <link type="text/css" rel="stylesheet" href="{swagger_css_url}">
    <link rel="shortcut icon" href="{swagger_favicon_url}">
    <title>{title}</title>
    </head>
    <body>
    <div id="swagger-ui">
    </div>
    <script src="{swagger_js_url}"></script>
    <!-- `SwaggerUIBundle` is now available on the page -->
    <script>
    const ui = SwaggerUIBundle({{
        url: '{openapi_url}',
    """

    if oauth2_redirect_url:
        html += f"oauth2RedirectUrl: window.location.origin + '{oauth2_redirect_url}',"

    html += """
        dom_id: '#swagger-ui',
        presets: [
        SwaggerUIBundle.presets.apis,
        SwaggerUIBundle.SwaggerUIStandalonePreset
        ],
        layout: "BaseLayout",
        deepLinking: true
    })"""

    if init_oauth:
        html += f"""
        ui.initOAuth({json.dumps(json.loads(init_oauth))})
        """

    html += """
    </script>
    </body>
    </html>
    """
    return html


@openapi_bp.route("/openapi.json")
def openapi():
    return jsonify(openapi_spec)


@openapi_bp.route("/docs")
def swagger_ui():
    return Response(
        get_swagger_ui_html(
            openapi_url=url_for("openapi_blueprint.openapi"),
            title=current_app.config["TITLE"],
        )
    )
