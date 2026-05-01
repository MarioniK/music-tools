#!/usr/bin/env bash
set -u

usage() {
  cat <<'USAGE'
Usage:
  scripts/runtime_validation/classify_fixture.sh BASE_URL FIXTURE_PATH OUTPUT_DIR [LABEL] [REPEAT_COUNT]

Examples:
  scripts/runtime_validation/classify_fixture.sh http://127.0.0.1:8021 app/tmp/upload.mp3 docs/runtime/evidence/roadmap-3.5/baseline upload 10
  scripts/runtime_validation/classify_fixture.sh http://127.0.0.1:8121 /tmp/roadmap-3.5-fixtures/fake.mp3 docs/runtime/evidence/roadmap-3.5/candidate-py312-etf fake 0
USAGE
}

if [ "$#" -lt 3 ] || [ "$#" -gt 5 ]; then
  usage >&2
  exit 2
fi

BASE_URL="${1%/}"
FIXTURE_PATH="$2"
OUTPUT_DIR="$3"
LABEL="${4:-$(basename "$FIXTURE_PATH")}"
REPEAT_COUNT="${5:-0}"

if ! command -v curl >/dev/null 2>&1; then
  echo "curl is required" >&2
  exit 127
fi

if [ ! -f "$FIXTURE_PATH" ]; then
  echo "fixture not found: $FIXTURE_PATH" >&2
  exit 2
fi

case "$REPEAT_COUNT" in
  ''|*[!0-9]*)
    echo "REPEAT_COUNT must be a non-negative integer" >&2
    exit 2
    ;;
esac

mkdir -p "$OUTPUT_DIR"

write_request() {
  request_name="$1"
  body_path="$OUTPUT_DIR/${request_name}.body.json"
  meta_path="$OUTPUT_DIR/${request_name}.meta.txt"

  curl -sS \
    -o "$body_path" \
    -w 'HTTP_STATUS:%{http_code}\nTIME_TOTAL:%{time_total}\n' \
    -F "file=@${FIXTURE_PATH}" \
    "${BASE_URL}/classify" >"$meta_path"
}

curl -sS \
  -o "$OUTPUT_DIR/health.body.json" \
  -w 'HTTP_STATUS:%{http_code}\nTIME_TOTAL:%{time_total}\n' \
  "${BASE_URL}/health" >"$OUTPUT_DIR/health.meta.txt"

write_request "${LABEL}.classify"

i=1
while [ "$i" -le "$REPEAT_COUNT" ]; do
  write_request "${LABEL}.repeat-${i}"
  i=$((i + 1))
done

{
  echo "base_url=$BASE_URL"
  echo "fixture_path=$FIXTURE_PATH"
  echo "label=$LABEL"
  echo "repeat_count=$REPEAT_COUNT"
  echo "captured_at_utc=$(date -u '+%Y-%m-%dT%H:%M:%SZ')"
} >"$OUTPUT_DIR/${LABEL}.run.txt"
