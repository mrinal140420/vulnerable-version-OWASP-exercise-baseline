#!/usr/bin/env bash
set -e
python3 -m venv venv
. venv/bin/activate
pip install -r requirements.txt
export FLASK_APP=app.py
export FLASK_ENV=development
flask run --host=127.0.0.1 --port=5000