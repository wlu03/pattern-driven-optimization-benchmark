#!/usr/bin/env bash
# setup_randomization.sh — Mytkowicz-style setup randomization for one pattern.
#
# Varies link order (3-4 orderings) and UNIX environment padding (4 sizes)
# producing 12-16 (slow_ms, fast_ms) measurements per pattern that can be
# fed into bootstrap_speedup_ci.py for a defensible speedup claim.
#
# Reference:
#   Mytkowicz, Diwan, Hauswirth, Sweeney. "Producing Wrong Data Without
#   Doing Anything Obviously Wrong!" ASPLOS 2009, DOI 10.1145/1508244.1508275.
#   Their finding: varying ONLY link order can flip the sign of -O3 vs -O2
#   on perlbench; varying ONLY UNIX env padding shifts timings by 33% routine
#   / up to 300% extreme. Single-setup speedups < ~10% are not trustworthy
#   without setup randomization.
#
# Usage:
#   scripts/setup_randomization.sh <pattern_id> [output_dir]
#
# Output:
#   <output_dir>/setup_runs.csv with columns:
#     setup_id, link_order, env_pad_size, slow_ms, fast_ms, speedup
#
# Pipe into bootstrap CI:
#   python3 scripts/bootstrap_speedup_ci.py --runs-csv $OUT/setup_runs.csv \
#       --slow-col slow_ms --fast-col fast_ms

set -euo pipefail

PATTERN_ID="${1:-SR-1}"
OUT_DIR="${2:-/tmp/setup_rand_${PATTERN_ID}}"
REPO_ROOT="$(cd "$(dirname "$0")/.." && pwd)"

mkdir -p "$OUT_DIR"
OUT_CSV="$OUT_DIR/setup_runs.csv"

# Find any on-disk variant of this pattern to use as the canonical inputs
VARIANT_DIR=$(find "$REPO_ROOT/dataset" -type d -name "${PATTERN_ID}_v*" \
              | sort | head -1)
if [ -z "$VARIANT_DIR" ]; then
  echo "No on-disk variant found for pattern $PATTERN_ID under $REPO_ROOT/dataset/" >&2
  exit 1
fi
echo "Pattern:  $PATTERN_ID"
echo "Variant:  $VARIANT_DIR"
echo "Output:   $OUT_CSV"
echo

cd "$OUT_DIR"
cp "$VARIANT_DIR"/{slow,fast,test}.c .
[ -f "$VARIANT_DIR/helper.c" ] && cp "$VARIANT_DIR/helper.c" .

# Prepend headers when the variant's slow.c / fast.c doesn't include them
# (most variants omit them because the generator pipeline expected the test
# harness to provide includes when inlining). Mirrors batch_test.py's
# _C_HEADERS-prepend logic so all 27 patterns compile standalone.
C_HEADERS='#include <stdio.h>
#include <stdlib.h>
#include <math.h>
#include <string.h>

'
for src in slow.c fast.c; do
    if ! grep -q '#include' "$src" 2>/dev/null; then
        { printf '%s' "$C_HEADERS"; cat "$src"; } > "$src.tmp" && mv "$src.tmp" "$src"
    fi
done

# Inline extern decls into test.c. Uses the plural extract_extern_decls
# (added to batch_test.py to support multi-public-function patterns) so
# every public function in slow.c / fast.c gets declared. For single-function
# patterns (the common case) plural and single produce the same result.
SLOW_DECL=$(python3 -c "
import sys; sys.path.insert(0, '$REPO_ROOT/scripts')
from batch_test import extract_extern_decls
print(extract_extern_decls(open('slow.c').read()))
")
FAST_DECL=$(python3 -c "
import sys; sys.path.insert(0, '$REPO_ROOT/scripts')
from batch_test import extract_extern_decls
print(extract_extern_decls(open('fast.c').read()))
")
# Use python for the substitution — sed chokes on the parens in the decls
python3 -c "
t = open('test.c').read()
t = t.replace('// SLOW_CODE_HERE', '''$SLOW_DECL''')
t = t.replace('// FAST_CODE_HERE', '''$FAST_DECL''')
open('test_decls.c','w').write(t)
"

# Link orderings to sweep (Mytkowicz §4.1 — link order shifts code placement)
if [ -f helper.c ]; then
  LINK_ORDERS=(
    "test_decls.c slow.c fast.c helper.c"
    "fast.c slow.c test_decls.c helper.c"
    "helper.c test_decls.c slow.c fast.c"
    "slow.c helper.c fast.c test_decls.c"
  )
else
  LINK_ORDERS=(
    "test_decls.c slow.c fast.c"
    "fast.c slow.c test_decls.c"
    "slow.c fast.c test_decls.c"
  )
fi

# Environment paddings (Mytkowicz §4.2 — env loads before stack)
ENV_PADS=(0 64 256 1024)

echo "setup_id,link_order,env_pad_size,slow_ms,fast_ms,speedup" > "$OUT_CSV"

SETUP_ID=0
FAILED=0
for ORDER in "${LINK_ORDERS[@]}"; do
  for PAD in "${ENV_PADS[@]}"; do
    SETUP_ID=$((SETUP_ID + 1))
    BIN="bench_${SETUP_ID}"

    if ! gcc -O2 -fno-lto -o "$BIN" $ORDER -lm 2>/tmp/.gcc_err_$$; then
      FAILED=$((FAILED + 1))
      echo "  setup $SETUP_ID: COMPILE FAIL ($(head -1 /tmp/.gcc_err_$$))" >&2
      rm -f /tmp/.gcc_err_$$
      continue
    fi
    rm -f /tmp/.gcc_err_$$

    if [ "$PAD" -eq 0 ]; then
      OUT=$(./"$BIN" 2>&1) || { FAILED=$((FAILED+1)); continue; }
    else
      PAD_VAL=$(printf 'X%.0s' $(seq 1 "$PAD"))
      OUT=$(env BENCH_PAD="$PAD_VAL" ./"$BIN" 2>&1) \
        || { FAILED=$((FAILED+1)); continue; }
    fi

    SLOW_MS=$(echo "$OUT" | grep -oE 'slow_ms=[0-9.]+' | head -1 | cut -d= -f2)
    FAST_MS=$(echo "$OUT" | grep -oE 'fast_ms=[0-9.]+' | head -1 | cut -d= -f2)
    SPEEDUP=$(echo "$OUT" | grep -oE 'speedup=[0-9.]+' | head -1 | cut -d= -f2)

    if [ -n "$SLOW_MS" ] && [ -n "$FAST_MS" ]; then
      # Order tag: hash the file list for a short stable identifier
      ORDER_TAG=$(echo "$ORDER" | tr -d ' .c_' | head -c 12)
      echo "$SETUP_ID,$ORDER_TAG,$PAD,$SLOW_MS,$FAST_MS,$SPEEDUP" >> "$OUT_CSV"
      printf "  setup %2d  order=%-15s pad=%5d  slow=%8.3f fast=%8.3f sp=%s\n" \
        "$SETUP_ID" "$ORDER_TAG" "$PAD" "$SLOW_MS" "$FAST_MS" "$SPEEDUP"
    else
      FAILED=$((FAILED + 1))
    fi
    rm -f "$BIN"
  done
done

# Cleanup intermediate sources
rm -f slow.c fast.c test.c test_decls.c helper.c

echo
echo "Wrote $((SETUP_ID - FAILED))/$SETUP_ID setups to $OUT_CSV"
echo
echo "Bootstrap CI on the distribution (rejects claim if CI crosses 1.0):"
echo "  python3 $REPO_ROOT/scripts/bootstrap_speedup_ci.py \\"
echo "      --runs-csv $OUT_CSV --slow-col slow_ms --fast-col fast_ms"
