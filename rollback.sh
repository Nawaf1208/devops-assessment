#!/usr/bin/env bash

set -euo pipefail

if [ ! -f PREVIOUS_VERSION ]; then
    echo "ERROR: No PREVIOUS_VERSION recorded. Cannot roll back."
    exit 1
fi

GOOD_VERSION=$(cat PREVIOUS_VERSION)
COMPOSE_CMD=(docker compose -f docker-compose.prod.yml --env-file ./backend/.env)

echo "Rolling back to previous version: $GOOD_VERSION"

IMAGE_TAG="$GOOD_VERSION" "${COMPOSE_CMD[@]}" down
IMAGE_TAG="$GOOD_VERSION" "${COMPOSE_CMD[@]}" pull
IMAGE_TAG="$GOOD_VERSION" "${COMPOSE_CMD[@]}" up -d

echo "$GOOD_VERSION" > CURRENT_VERSION
echo "Waiting for services to start..."
sleep 15

echo "Verifying rollback..."
BACKEND_HEALTH=$(curl -s -o /dev/null -w "%{http_code}" http://api.debyez.localhost/api/health/full || echo "000")
FRONTEND_HEALTH=$(curl -s -o /dev/null -w "%{http_code}" http://app.debyez.localhost/ || echo "000")

if [ "$BACKEND_HEALTH" = "200" ] && [ "$FRONTEND_HEALTH" = "200" ]; then
  echo "Rollback verified healthy."
  echo "Current version restored to: $(cat CURRENT_VERSION)"
else
  echo "WARNING: Rollback completed but health checks failed (backend: $BACKEND_HEALTH, frontend: $FRONTEND_HEALTH)."
  echo "Manual investigation required."
  exit 1
fi