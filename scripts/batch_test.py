"""Batch test all generated variants and produce summary report.

Compiles slow.c, fast.c, and test.c as THREE SEPARATE TRANSLATION UNITS
with -fno-lto so the compiler cannot inline or perform cross-function
optimizations across file boundaries. This ensures the measured inefficiency
is genuine and not already optimized away by the compiler.
"""
import os, sys, json, subprocess, tempfile, csv, re
from collections import defaultdict

DATASET_DIR = sys.argv[1] if len(sys.argv) > 1 else "dataset"

# Headers prepended to slow.c / fast.c so they compile standalone.
# The on-disk files may omit these (they're just function bodies).
_C_HEADERS = "#include <stdio.h>\n#include <stdlib.h>\n#include <math.h>\n#include <string.h>\n\n"

def extract_extern_decl(code):
    """Turn a function definition into an extern forward declaration.

    Robust against files that include #include headers, blank lines,
    __attribute__((noinline)) prefixes, and typedef struct definitions
    added by the generator pipeline.

    Strategy: scan lines top-to-bottom, resetting whenever we see a
    preprocessor directive or a standalone __attribute__ line, then capture
    everything up to (but not including) the first '{' that belongs to a
    function (not a struct/enum/union definition).
    """
    sig_parts = []
    in_block = 0  # brace-nesting depth for skipping struct/enum/union blocks
    for line in code.split('\n'):
        stripped = line.strip()
        # Skip lines inside a struct/enum/union block
        if in_block > 0:
            in_block += stripped.count('{') - stripped.count('}')
            if in_block < 0:
                in_block = 0
            continue
        # Preprocessor, standalone attribute, or comment line — reset and keep scanning
        if stripped.startswith('#') or stripped.startswith('__attribute__') or \
                stripped.startswith('//') or stripped.startswith('/*'):
            sig_parts = []
            continue
        if not stripped:
            if sig_parts:
                sig_parts = []   # blank line between attribute and sig: reset
            continue
        # Detect typedef struct/union/enum or standalone struct/union/enum definition
        lower = stripped.lower()
        is_type_def = (lower.startswith('typedef struct') or
                       lower.startswith('typedef union') or
                       lower.startswith('typedef enum') or
                       (lower.startswith('struct ') and '{' in stripped) or
                       (lower.startswith('union ') and '{' in stripped) or
                       (lower.startswith('enum ') and '{' in stripped))
        if is_type_def and '{' in stripped:
            # Enter the block, reset sig_parts, skip until closing '}'
            in_block = stripped.count('{') - stripped.count('}')
            sig_parts = []
            continue
        if '{' in stripped and not stripped.startswith('//'):
            before = stripped[:stripped.index('{')].strip()
            if before:
                sig_parts.append(before)
            # Skip static (file-local) helper functions — keep scanning for
            # the first public (non-static) function definition.
            candidate = ' '.join(sig_parts).strip()
            if re.search(r'\bstatic\b', candidate):
                sig_parts = []
                # Track brace depth to skip this function body entirely
                depth = stripped.count('{') - stripped.count('}')
                if depth > 0:
                    in_block = depth
                continue
            break
        sig_parts.append(stripped)

    sig = ' '.join(sig_parts).strip()
    return f"extern {sig};"

results = []
errors = []

# Find all variant directories
print(f"  {'':2} {'Variant':<22} {'Speedup -O0':>12}  {'Speedup -O3':>12}  {'Difficulty'}")
print(f"  {'-'*2} {'-'*22} {'-'*12}  {'-'*12}  {'-'*10}")

for root, dirs, files in os.walk(DATASET_DIR):
    if "metadata.json" in files and "slow.c" in files:
        meta = json.load(open(os.path.join(root, "metadata.json")))
        slow = open(os.path.join(root, "slow.c")).read()
        fast = open(os.path.join(root, "fast.c")).read()
        test_path = os.path.join(root, "test.c")

        if not os.path.exists(test_path):
            continue
        test = open(test_path).read()
        if "SLOW_CODE_HERE" not in test:
            continue

        # Replace inline placeholders with extern declarations so test.c
        # cannot see the function bodies at compile time.
        slow_decl = extract_extern_decl(slow)
        fast_decl = extract_extern_decl(fast)
        test_with_decls = (test
            .replace("// SLOW_CODE_HERE", slow_decl)
            .replace("// FAST_CODE_HERE", fast_decl))

        with tempfile.TemporaryDirectory() as tmp:
            # Three separate translation units
            slow_src = os.path.join(tmp, "slow.c")
            fast_src = os.path.join(tmp, "fast.c")
            test_src = os.path.join(tmp, "test.c")
            helper_path = os.path.join(root, "helper.c")

            with open(slow_src, "w") as f:
                # Prepend headers if not already present
                prefix = _C_HEADERS if "#include" not in slow else ""
                f.write(prefix + slow)
            with open(fast_src, "w") as f:
                prefix = _C_HEADERS if "#include" not in fast else ""
                f.write(prefix + fast)
            with open(test_src, "w") as f:
                f.write(test_with_decls)

            row = {
                "variant_id": meta["variant_id"],
                "pattern_id": meta["pattern_id"],
                "category": meta["category"],
                "difficulty": meta["difficulty"],
                "compiles_O0": False, "compiles_O3": False,
                "correct_O0": False, "correct_O3": False,
                "speedup_O0": 0, "speedup_O3": 0,
            }

            for opt in ["-O0", "-O3"]:
                tag = opt.replace("-", "")
                bin_path = os.path.join(tmp, f"test{opt}")
                # -fno-lto: prevent link-time inlining across TU boundaries
                extra_tus = [helper_path] if os.path.exists(helper_path) else []
                r = subprocess.run(
                    ["gcc", opt, "-fno-lto", "-o", bin_path,
                     test_src, slow_src, fast_src] + extra_tus + ["-lm"],
                    capture_output=True, text=True, timeout=10)
                if r.returncode != 0:
                    errors.append(f"{meta['variant_id']} compile {opt}: {r.stderr[:100]}")
                    continue
                row[f"compiles_{tag}"] = True

                try:
                    r = subprocess.run([bin_path], capture_output=True, text=True, timeout=60)
                except subprocess.TimeoutExpired:
                    errors.append(f"{meta['variant_id']} run {opt}: timed out (>60s)")
                    continue
                if r.returncode != 0:
                    errors.append(f"{meta['variant_id']} run {opt}: timeout/error")
                    continue

                parts = dict(p.split("=") for p in r.stdout.strip().split() if "=" in p)
                row[f"correct_{tag}"] = parts.get("correct", "0") == "1"
                row[f"speedup_{tag}"] = float(parts.get("speedup", "0"))

            results.append(row)
            status = "✓" if row["correct_O0"] else "✗"
            compiler_resistant = "  ← compiler-resistant" if row["speedup_O3"] > 2.0 else "  ← compiler fixes this"
            print(f"  {status} {meta['variant_id']:<22} fast/slow -O0: {row['speedup_O0']:6.1f}x  fast/slow -O3: {row['speedup_O3']:6.1f}x  [{meta['difficulty']}]{compiler_resistant}")


total = len(results)
correct = sum(1 for r in results if r['correct_O0'])
resistant = sum(1 for r in results if r['speedup_O3'] > 2.0)
print(f"\n{'='*90}")
print(f"Summary: {total} variants tested  |  {correct}/{total} correct  |  {resistant}/{total} compiler-resistant at -O3")
print(f"  (compiler-resistant = fast/slow speedup remains >2x even at -O3)\n")

by_pattern = defaultdict(list)
for r in results:
    by_pattern[r["pattern_id"]].append(r)

print(f"{'Pattern':<10} {'Variants':>8} {'Correct':>8} {'Avg fast/slow -O0':>18} {'Avg fast/slow -O3':>18}  {'Compiler-resistant?'}")
print("-" * 90)
for pid in sorted(by_pattern.keys()):
    rows = by_pattern[pid]
    n = len(rows)
    corr = sum(1 for r in rows if r["correct_O0"])
    avg_o0 = sum(r["speedup_O0"] for r in rows if r["correct_O0"]) / max(corr, 1)
    avg_o3 = sum(r["speedup_O3"] for r in rows if r["correct_O3"]) / max(corr, 1)
    resistant_flag = "yes" if avg_o3 > 2.0 else "no — compiler closes the gap"
    print(f"{pid:<10} {n:>8} {corr:>8} {avg_o0:>17.1f}x {avg_o3:>17.1f}x  {resistant_flag}")

if errors:
    print(f"\n{len(errors)} errors:")
    for e in errors[:10]:
        print(f"  {e}")
