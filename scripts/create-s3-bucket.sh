#!/usr/bin/env bash
set -euo pipefail

if [[ $# -lt 1 ]]; then
  echo "Usage: $0 <bucket-name>" >&2
  exit 1
fi

BUCKET="$1"
ENDPOINT="${MOTO_ENDPOINT:-http://localhost:5000}"

AWS_ACCESS_KEY_ID=test AWS_SECRET_ACCESS_KEY=test aws --endpoint-url "$ENDPOINT" s3 mb "s3://${BUCKET}"
