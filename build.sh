#!/usr/bin/env bash
# Render build komutu — ortam değişkenlerinde DATABASE_URL tanımlı olmalı.
set -o errexit

pip install -r requirements.txt

python manage.py collectstatic --no-input
python manage.py migrate --no-input
python manage.py ensure_admin
python manage.py seed_gallery --force-gallery
