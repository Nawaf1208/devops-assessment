#!/usr/bin/env bash

set -euo pipefail

if [ -z "${1:-}" ]; then
    echo "Usage: ./deploy.sh <image-sha-tag>"
    exit 1
fi

NEW_VERSION="$1"
COMPOSE_CMD=(docker compose -f docker-compose.prod.yml --env-file ./backend/.env)

if [ -f CURRENT_VERSION ]; then
    cp CURRENT_VERSION PREVIOUS_VERSION
    echo "Backed up previous version: $(cat PREVIOUS_VERSION)"
fi

echo "$NEW_VERSION" > CURRENT_VERSION
echo "Deploying version: $NEW_VERSION"

IMAGE_TAG="$NEW_VERSION" "${COMPOSE_CMD[@]}" down
IMAGE_TAG="$NEW_VERSION" "${COMPOSE_CMD[@]}" pull
IMAGE_TAG="$NEW_VERSION" "${COMPOSE_CMD[@]}" up -d

echo ""
echo "Deployed: $(cat CURRENT_VERSION)"
if [ -f PREVIOUS_VERSION ]; then
    echo "Previous: $(cat PREVIOUS_VERSION)"
fi