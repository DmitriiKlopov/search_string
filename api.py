# -*- coding: utf-8 -*-
import logging
import os
from contextlib import closing

import psycopg2
import sentry_sdk
from flask import Flask, jsonify, request
from sentry_sdk.integrations.flask import FlaskIntegration

from .openapi import openapi_bp
from .search_string.config import SearchEngineConfig
from .search_string.search_engine import SearchEngine


logging.basicConfig(level=os.environ.get("LOG_LEVEL", "INFO"))

# Initialize sentry
sentry_sdk.init(integrations=[FlaskIntegration()])
sentry_sdk.capture_message("Sentry initialized", level="debug")

config = SearchEngineConfig()
search_engine = SearchEngine(config)

app = Flask(__name__)
app.config["TITLE"] = "search-gw-svc"
app.register_blueprint(openapi_bp)


@app.route("/health")
def health():
    r = jsonify({"status": "pass", "description": "rec-navigator-back"})
    r.mimetype = "application/health+json"
    return r


@app.route("/search", methods=["POST"])
def search():
    body = request.json
    search_string = body.get("search_string")
    search_index_names_par = body.get("search_index_names_par")
    return jsonify(search_engine.search(search_string, search_index_names_par))


@app.route("/search/extra", methods=["POST"])
def extra():
    body = request.json
    search_string = body.get("search_string")
    code = body.get("code")
    return jsonify(search_engine.search_extra(search_string, code))


@app.route("/send_feedback", methods=["POST"])
def get_feedback():
    body = request.json
    system = body.get("system")
    search_string = body.get("search_string")
    search_index_names_par = body.get("search_index_names_par")
    search_method = body.get("search_method")
    id = body.get("id")
    user_id = body.get("user_id")
    with closing(psycopg2.connect(dbname='services_dev', user='search-line-su',
                                  password='search-line-su', host='10.1.25.101', port='5432', )) as conn:
        with conn.cursor() as cursor:
            conn.autocommit = True
            # del_data = """DELETE FROM data_vault.sl_feedback"""
            # cursor.execute(del_data)
            result = system, search_index_names_par, id, search_method, search_string, user_id
            print("RESULT", result)
            cursor.execute(
                """INSERT INTO search_line.sl_feedback (system, search_index_names_par, id, search_method, search_string, user_id) VALUES (
                %s, %s, %s, %s, %s, %s)""", result
        )
    return jsonify(result)


@app.route("/change_data", methods=["POST"])

# def new_data():
#     with open("search_string/data.json", "r") as con:
#         data = json.load(con)
#         keys = data[0].keys()
#         index = keys
#         print(keys)
#     return jsonify(data)

def add_data():
    body = request.json
    access = body.get("access")
    block = body.get("block")
    create_date = body.get("create_date")
    description = body.get("description")
    fulltext = body.get("fulltext")
    header = body.get("header")
    id = body.get("id")
    logo = body.get("logo")
    phrases = body.get("phrases")
    priority = body.get("priority")
    tags = body.get("tags")
    time_to_live = body.get("time_to_live")
    url = body.get("url")
    with closing(psycopg2.connect(dbname='services_dev', user='search-line-su',
                                  password='search-line-su', host='10.1.25.101', port='5432', )) as conn:
        with conn.cursor() as cursor:
            conn.autocommit = True

            # del_data = """DELETE FROM search_line.test_add_data"""
            # cursor.execute(del_data)
            data = access, block, create_date, description, fulltext, header, id, logo, phrases, priority, tags, time_to_live, url
            result = data

            print("SSSS====", result)

            cursor.execute("""INSERT INTO search_line.test_add_data (access, block, create_date, description, fulltext,
            header, id, logo, phrases, priority, tags, time_to_live, url) VALUES
            (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)""", result)

    return jsonify(result)


@app.route("/delete_data", methods=["DELETE"])
def delete_data():
    body = request.json
    id = body.get("id")
    print(id)
    with closing(psycopg2.connect(dbname='services_dev', user='search-line-su',
                                  password='search-line-su', host='10.1.25.101', port='5432', )) as conn:
        with conn.cursor() as cursor:
            conn.autocommit = True

            del_data = """DELETE FROM search_line.test_add_data WHERE id = 'd290f1ee-6c54-4b01-90e6-d701748f0851'"""
            cursor.execute(del_data)


@app.route("/update_data", methods=["PUT"])
def update_data():
    body = request.json
    id = body.get("id")
    print(id)
    with closing(psycopg2.connect(dbname='services_dev', user='search-line-su',
                                  password='search-line-su', host='10.1.25.101', port='5432', )) as conn:
        with conn.cursor() as cursor:
            conn.autocommit = True

            del_data = """UPDATE search_line.test_add_data SET priority = 200 WHERE id = 'd290f1ee-6c54-4b01-90e6-d701748f0851'"""
            cursor.execute(del_data)


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8080)
