#!/usr/bin/env bash
set -euo pipefail
# ---------------------------------------------------------------------------
# Create an S3 bucket in the local Moto mock service.
#
# Usage:
#   ./scripts/create-s3-bucket.sh <bucket-name>
#
# Environment variables:
#   S3_AWS_ENDPOINT_URL  – S3 endpoint URL (default: http://localhost:5000)
# ---------------------------------------------------------------------------

if [[ $# -lt 1 ]]; then
  echo "Usage: $0 <bucket-name>" >&2
  exit 1
fi

BUCKET="$1"
ENDPOINT="${S3_AWS_ENDPOINT_URL:-http://localhost:5000}"

echo "Creating bucket '${BUCKET}' at ${ENDPOINT} ..."
AWS_ACCESS_KEY_ID=test AWS_SECRET_ACCESS_KEY=test \
  aws --endpoint-url "$ENDPOINT" s3 mb "s3://${BUCKET}"
echo "Bucket '${BUCKET}' created successfully."
