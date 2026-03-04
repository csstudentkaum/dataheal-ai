#!/usr/bin/env bash
# Exit on error
set -o errexit

pip install -r requirements.txt

# Create media directory for uploads
mkdir -p media/uploads

python manage.py collectstatic --no-input
python manage.py makemigrations --no-input
python manage.py migrate --no-input
