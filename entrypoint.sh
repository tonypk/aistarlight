#!/bin/sh
set -e

export PYTHONPATH=/app

echo "Running database migrations..."
alembic -c alembic.ini upgrade head

echo "Starting application..."
exec "$@"
