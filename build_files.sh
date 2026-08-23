#!/bin/bash
# Vercel build step: install deps and collect static files.
set -e
python3 -m pip install --upgrade pip
python3 -m pip install -r requirements.txt
python3 manage.py collectstatic --noinput --clear
