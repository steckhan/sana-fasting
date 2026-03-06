#!/usr/bin/env bash
set -euo pipefail

# Ingest PDF into knowledge folder and index immediately.
# Usage: ./tools/ingest-pdf.sh /path/to/file.pdf [slug]

PDF_PATH="${1:-}"
SLUG="${2:-}"

if [[ -z "$PDF_PATH" ]]; then
  echo "Usage: $0 /path/to/file.pdf [slug]" >&2
  exit 1
fi

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"

if [[ -n "$SLUG" ]]; then
  "$SCRIPT_DIR/pdf-to-memory.sh" "$PDF_PATH" knowledge "$SLUG" --index
else
  "$SCRIPT_DIR/pdf-to-memory.sh" "$PDF_PATH" knowledge "" --index
fi
