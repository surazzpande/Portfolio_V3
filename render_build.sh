#!/usr/bin/env bash
# Render build step. Runs on every deploy.
set -o errexit

pip install --upgrade pip
pip install -r requirements.txt

# Collect static files for WhiteNoise to serve.
python manage.py collectstatic --no-input

# Apply database migrations. Safe to run repeatedly.
python manage.py migrate

# Load the portfolio content the first time only. seed uses update_or_create,
# so re-running never duplicates anything and never overwrites your edits
# to contact messages or users.
python manage.py seed

# Create the admin user, if DJANGO_SUPERUSER_* are set in the Render dashboard.
# Django's createsuperuser reads those three variables natively. It exits
# non-zero when the user already exists, which is fine on redeploys.
python manage.py createsuperuser --no-input || echo "Admin user already exists - skipping."
