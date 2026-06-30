#!/usr/bin/env bash

# Exit immediately if a command exits with a non-zero status
set -e

echo "Applying database migrations..."
python manage.py migrate --noinput

echo "Syncing votes to Redis..."
python manage.py sync_votes_to_redis || echo "Redis sync failed (non-fatal)"

echo "Starting server..."
exec "$@"
