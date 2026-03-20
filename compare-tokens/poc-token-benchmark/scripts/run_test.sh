#!/usr/bin/env bash
# =============================================================================
# run_test.sh
#
# Token benchmark runner for macOS, Linux and WSL2.
#
# Usage:
#   bash scripts/run_test.sh <variant>
#
# Variants:
#   lf          LF line endings, no BOM   (baseline)
#   crlf        CRLF line endings, no BOM
#   lf_bom      LF line endings, UTF-8 BOM
#   crlf_bom    CRLF line endings, UTF-8 BOM
#
# Prerequisites:
#   - claude CLI installed and authenticated
#   - python3 in PATH
#   - Variants generated: python scripts/generate_variants.py
#
# Example:
#   bash scripts/run_test.sh lf
#   bash scripts/run_test.sh crlf
# =============================================================================

set -euo pipefail

# ── Paths ────────────────────────────────────────────────────────────────────
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT_DIR="$(dirname "$SCRIPT_DIR")"
VARIANTS_DIR="$ROOT_DIR/variants"
RESULTS_DIR="$ROOT_DIR/results"
TEST_PROJECT="$ROOT_DIR/test_project"

# ── Validate input ───────────────────────────────────────────────────────────
VARIANT="${1:-}"
VALID=("lf" "crlf" "lf_bom" "crlf_bom")

if [[ -z "$VARIANT" ]]; then
    echo "Usage: bash scripts/run_test.sh <variant>"
    echo "Variants: ${VALID[*]}"
    exit 1
fi

FOUND=0
for v in "${VALID[@]}"; do [[ "$v" == "$VARIANT" ]] && FOUND=1; done
if [[ $FOUND -eq 0 ]]; then
    echo "ERROR: Unknown variant '$VARIANT'. Valid: ${VALID[*]}"
    exit 1
fi

VARIANT_FILE="$VARIANTS_DIR/claude_${VARIANT}.md"
if [[ ! -f "$VARIANT_FILE" ]]; then
    echo "ERROR: Variant file not found: $VARIANT_FILE"
    echo "       Run first: python scripts/generate_variants.py"
    exit 1
fi

# ── Environment detection ─────────────────────────────────────────────────────
detect_env() {
    if [[ -f /proc/version ]] && grep -qi microsoft /proc/version 2>/dev/null; then
        echo "wsl2"
    elif [[ "$(uname -s)" == "Darwin" ]]; then
        echo "macos"
    else
        echo "linux"
    fi
}

ENV_NAME=$(detect_env)
OS_INFO=$(uname -a)
TIMESTAMP=$(date -u +"%Y%m%dT%H%M%SZ")
RESULT_FILE="$RESULTS_DIR/${ENV_NAME}_${VARIANT}_${TIMESTAMP}.json"

mkdir -p "$RESULTS_DIR" "$TEST_PROJECT"

# ── File metadata ─────────────────────────────────────────────────────────────
FILE_SIZE=$(wc -c < "$VARIANT_FILE" | tr -d ' ')
LINE_COUNT=$(wc -l < "$VARIANT_FILE" | tr -d ' ')
HAS_BOM=false
HAS_CRLF=false

# Check BOM (first 3 bytes: EF BB BF)
FIRST3=$(head -c 3 "$VARIANT_FILE" | xxd -p 2>/dev/null || od -An -N3 -tx1 "$VARIANT_FILE" | tr -d ' \n')
[[ "$FIRST3" == "efbbbf"* ]] && HAS_BOM=true

# Check CRLF
grep -Pq $'\r' "$VARIANT_FILE" 2>/dev/null && HAS_CRLF=true || true

# ── Setup test project ────────────────────────────────────────────────────────
cp "$VARIANT_FILE" "$TEST_PROJECT/CLAUDE.md"

echo "========================================================"
echo "  Claude Code Token Benchmark"
echo "========================================================"
echo "  Environment  : $ENV_NAME"
echo "  Variant      : $VARIANT"
echo "  File size    : $FILE_SIZE bytes"
echo "  Lines        : $LINE_COUNT"
echo "  Has BOM      : $HAS_BOM"
echo "  Has CRLF     : $HAS_CRLF"
echo "  Timestamp    : $TIMESTAMP"
echo "========================================================"
echo ""

# ── Run claude and measure time ───────────────────────────────────────────────
# Fixed, minimal prompt to keep output tokens constant across all runs
PROMPT="Respond with exactly one word: READY"

echo "  Prompt : $PROMPT"
echo "  Running..."
echo ""

# Record timestamp BEFORE the run (used to find the new session file)
BEFORE_TS=$(date +%s)

START_NS=$(date +%s%N 2>/dev/null || python3 -c "import time; print(int(time.time()*1e9))")

CLAUDE_OUTPUT=$(cd "$TEST_PROJECT" && claude --print "$PROMPT" 2>&1)

END_NS=$(date +%s%N 2>/dev/null || python3 -c "import time; print(int(time.time()*1e9))")

DURATION_MS=$(( (END_NS - START_NS) / 1000000 ))
DURATION_SEC=$(python3 -c "print(f'{$DURATION_MS / 1000:.3f}')")

echo "  Claude output : $CLAUDE_OUTPUT"
echo "  Duration      : ${DURATION_SEC}s"
echo ""

# ── Parse token usage from session JSONL ─────────────────────────────────────
echo "  Parsing session token usage..."

TOKENS_JSON=$(python3 "$SCRIPT_DIR/parse_session.py" --after "$BEFORE_TS")

if echo "$TOKENS_JSON" | python3 -c "import sys,json; d=json.load(sys.stdin); sys.exit(0 if 'error' not in d else 1)" 2>/dev/null; then
    INPUT_TOKENS=$(echo "$TOKENS_JSON"    | python3 -c "import sys,json; d=json.load(sys.stdin); print(d['input_tokens'])")
    OUTPUT_TOKENS=$(echo "$TOKENS_JSON"   | python3 -c "import sys,json; d=json.load(sys.stdin); print(d['output_tokens'])")
    CACHE_CREATE=$(echo "$TOKENS_JSON"    | python3 -c "import sys,json; d=json.load(sys.stdin); print(d['cache_creation_tokens'])")
    CACHE_READ=$(echo "$TOKENS_JSON"      | python3 -c "import sys,json; d=json.load(sys.stdin); print(d['cache_read_tokens'])")
    TOTAL_TOKENS=$(echo "$TOKENS_JSON"    | python3 -c "import sys,json; d=json.load(sys.stdin); print(d['total_tokens'])")
    SESSION_FILE=$(echo "$TOKENS_JSON"    | python3 -c "import sys,json; d=json.load(sys.stdin); print(d['session_file'])")
else
    echo "  WARNING: Could not parse session file. Token counts will be 0."
    INPUT_TOKENS=0; OUTPUT_TOKENS=0; CACHE_CREATE=0; CACHE_READ=0; TOTAL_TOKENS=0; SESSION_FILE="unknown"
fi

echo ""
echo "  ┌─────────────────────────────────┐"
echo "  │  Token Summary                  │"
echo "  ├─────────────────────────────────┤"
printf "  │  %-20s : %8s  │\n" "Input tokens"     "$INPUT_TOKENS"
printf "  │  %-20s : %8s  │\n" "Output tokens"    "$OUTPUT_TOKENS"
printf "  │  %-20s : %8s  │\n" "Cache creation"   "$CACHE_CREATE"
printf "  │  %-20s : %8s  │\n" "Cache read"       "$CACHE_READ"
printf "  │  %-20s : %8s  │\n" "Total"            "$TOTAL_TOKENS"
echo "  └─────────────────────────────────┘"
echo ""

# ── Save result ───────────────────────────────────────────────────────────────
python3 - <<PYEOF
import json, pathlib

result = {
    "environment": "$ENV_NAME",
    "os_info": "$OS_INFO",
    "timestamp": "$TIMESTAMP",
    "variant": "$VARIANT",
    "file_metadata": {
        "size_bytes": $FILE_SIZE,
        "line_count": $LINE_COUNT,
        "has_bom": $( [[ "$HAS_BOM" == "true" ]] && echo "true" || echo "false" ),
        "has_crlf": $( [[ "$HAS_CRLF" == "true" ]] && echo "true" || echo "false" ),
    },
    "duration_seconds": $DURATION_SEC,
    "claude_output": "$CLAUDE_OUTPUT",
    "tokens": {
        "input": $INPUT_TOKENS,
        "output": $OUTPUT_TOKENS,
        "cache_creation": $CACHE_CREATE,
        "cache_read": $CACHE_READ,
        "total": $TOTAL_TOKENS,
    },
    "session_file": "$SESSION_FILE",
}

out = pathlib.Path("$RESULT_FILE")
out.write_text(json.dumps(result, indent=2))
print(f"  Result saved : {out}")
PYEOF

echo ""
echo "  Next: run with another variant, then analyze:"
echo "  python scripts/analyze_results.py"
