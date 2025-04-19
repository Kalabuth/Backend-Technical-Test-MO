#!/usr/bin/env sh
set -e

echo "🛠️  Generating migrations…"
python manage.py makemigrations --noinput

echo "⏳  Applying migrations…"
python manage.py migrate --fake-initial --noinput

echo "✅  Migrations done. Starting $*"
exec "$@"
