#!/usr/bin/env bash
set -euo pipefail

BASE_URL="http://127.0.0.1:8000"
ENV_FILE="/opt/precificador/.env"
LOG_FILE="/var/log/precificador-refresh-ml.log"

TOKEN="$(grep '^INTERNAL_JOB_TOKEN=' "$ENV_FILE" | cut -d= -f2-)"

if [ -z "${TOKEN:-}" ]; then
  echo "$(date '+%Y-%m-%d %H:%M:%S') ERRO: INTERNAL_JOB_TOKEN nao encontrado no .env" >> "$LOG_FILE"
  exit 1
fi

RESPONSE="$(curl -sS -X POST "${BASE_URL}/oauth/ml/refresh?company=SP" -H "x-internal-token: ${TOKEN}")"
echo "$(date '+%Y-%m-%d %H:%M:%S') OK: ${RESPONSE}" >> "$LOG_FILE"
