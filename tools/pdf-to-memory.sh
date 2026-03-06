#!/usr/bin/env bash
set -euo pipefail

# Convert a PDF into Markdown chunks for memory indexing.
# Usage:
#   ./tools/pdf-to-memory.sh /path/to/file.pdf [knowledge|docs|notes] [slug] [--index]

PDF_PATH="${1:-}"
TARGET_DIR_NAME="${2:-knowledge}"
SLUG_INPUT="${3:-}"
INDEX_FLAG="${4:-}"

if [[ -z "$PDF_PATH" ]]; then
  echo "Usage: $0 /path/to/file.pdf [knowledge|docs|notes] [slug] [--index]" >&2
  exit 1
fi

if [[ ! -f "$PDF_PATH" ]]; then
  echo "Error: PDF not found: $PDF_PATH" >&2
  exit 1
fi

case "$TARGET_DIR_NAME" in
  knowledge|docs|notes) ;;
  *)
    echo "Error: target must be one of: knowledge | docs | notes" >&2
    exit 1
    ;;
esac

if [[ -n "$INDEX_FLAG" && "$INDEX_FLAG" != "--index" ]]; then
  echo "Error: 4th argument must be --index or omitted" >&2
  exit 1
fi

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
WORKSPACE="$(cd "$SCRIPT_DIR/.." && pwd)"
WORKSPACE_BASENAME="$(basename "$WORKSPACE")"
MEMORY_AGENT="${MEMORY_AGENT:-${WORKSPACE_BASENAME#workspace-}}"
TARGET_DIR="$WORKSPACE/$TARGET_DIR_NAME"
mkdir -p "$TARGET_DIR"

BASENAME="$(basename "$PDF_PATH")"
TITLE="${BASENAME%.*}"
DATE_STR="$(date +%F)"

slugify() {
  local s="$1"
  s="$(echo "$s" | tr '[:upper:]' '[:lower:]')"
  s="$(echo "$s" | sed -E 's/[^a-z0-9]+/-/g; s/^-+//; s/-+$//')"
  if [[ -z "$s" ]]; then s="document"; fi
  echo "$s"
}

if [[ -n "$SLUG_INPUT" ]]; then
  SLUG="$(slugify "$SLUG_INPUT")"
else
  SLUG="$(slugify "$TITLE")"
fi

TMP_TXT="$(mktemp)"
trap 'rm -f "$TMP_TXT"' EXIT

extract_with_pdftotext() {
  if command -v /opt/homebrew/bin/pdftotext >/dev/null 2>&1; then
    /opt/homebrew/bin/pdftotext "$PDF_PATH" -
    return $?
  elif command -v pdftotext >/dev/null 2>&1; then
    pdftotext "$PDF_PATH" -
    return $?
  fi
  return 1
}

if ! extract_with_pdftotext > "$TMP_TXT" 2>/dev/null; then
  if command -v /usr/bin/python3 >/dev/null 2>&1; then
    /usr/bin/python3 - "$PDF_PATH" > "$TMP_TXT" <<'PY'
import sys
try:
    from pypdf import PdfReader
except Exception:
    print("", end="")
    sys.exit(2)
path = sys.argv[1]
reader = PdfReader(path)
parts = []
for p in reader.pages:
    parts.append(p.extract_text() or "")
print("\n\n".join(parts))
PY
    rc=$?
    if [[ $rc -eq 2 ]]; then
      echo "Error: no PDF extractor available. Install poppler (pdftotext) or pypdf." >&2
      exit 1
    fi
  else
    echo "Error: text extraction failed and python3 is unavailable." >&2
    exit 1
  fi
fi

if [[ -z "$(tr -d '[:space:]' < "$TMP_TXT")" ]]; then
  echo "Error: extracted PDF text is empty." >&2
  exit 1
fi

PARTS_COUNT="$(/usr/bin/python3 - "$TMP_TXT" "$TARGET_DIR" "$SLUG" "$TITLE" "$PDF_PATH" "$DATE_STR" <<'PY'
import sys
from pathlib import Path

src = Path(sys.argv[1])
target = Path(sys.argv[2])
slug = sys.argv[3]
title = sys.argv[4]
pdf_path = sys.argv[5]
date_str = sys.argv[6]

text = src.read_text(errors="ignore")
text = " ".join(text.split())
chunk_size = 1200
chunks = [text[i:i+chunk_size] for i in range(0, len(text), chunk_size)]

for old in target.glob(f"{slug}-part-*.md"):
    old.unlink()

for i, chunk in enumerate(chunks, 1):
    out = target / f"{slug}-part-{i:03d}.md"
    out.write_text(
        f"# {title}\n\n"
        f"Source PDF: {pdf_path}  \n"
        f"Imported: {date_str}\n"
        f"Part: {i}/{len(chunks)}\n\n"
        f"---\n\n"
        f"{chunk}\n",
        encoding="utf-8"
    )

print(len(chunks))
PY
)"

echo "OK: imported $PARTS_COUNT chunk(s) to $TARGET_DIR as $SLUG-part-XXX.md"

if [[ "$INDEX_FLAG" == "--index" ]]; then
  echo "Indexing memory for agent: $MEMORY_AGENT"
  openclaw memory index --agent "$MEMORY_AGENT"
  echo "Index complete."
else
  echo "Skipped indexing. Run manually: openclaw memory index --agent $MEMORY_AGENT"
fi
