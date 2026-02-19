"""Batch test all generated variants and produce summary report."""
import os, sys, json, subprocess, tempfile, csv
from collections import defaultdict

DATASET_DIR = sys.argv[1] if len(sys.argv) > 1 else "dataset"

results = []
errors = []

# Find all variant directories
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

        full = test.replace("// SLOW_CODE_HERE", slow).replace("// FAST_CODE_HERE", fast)

        with tempfile.TemporaryDirectory() as tmp:
            src = os.path.join(tmp, "test.c")
            with open(src, "w") as f:
                f.write(full)

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
                r = subprocess.run(["gcc", opt, "-o", bin_path, src, "-lm"],
                                   capture_output=True, text=True, timeout=10)
                if r.returncode != 0:
                    errors.append(f"{meta['variant_id']} compile {opt}: {r.stderr[:100]}")
                    continue
                row[f"compiles_{tag}"] = True

                r = subprocess.run([bin_path], capture_output=True, text=True, timeout=60)
                if r.returncode != 0:
                    errors.append(f"{meta['variant_id']} run {opt}: timeout/error")
                    continue

                parts = dict(p.split("=") for p in r.stdout.strip().split() if "=" in p)
                row[f"correct_{tag}"] = parts.get("correct", "0") == "1"
                row[f"speedup_{tag}"] = float(parts.get("speedup", "0"))

            results.append(row)
            status = "✓" if row["correct_O0"] else "✗"
            print(f"  {status} {meta['variant_id']:20s}  O0: {row['speedup_O0']:8.1f}x  O3: {row['speedup_O3']:8.1f}x  [{meta['difficulty']}]")


print(f"\n{'='*70}")
print(f"results: {len(results)} variants tested, {sum(1 for r in results if r['correct_O0'])} correct")


by_pattern = defaultdict(list)
for r in results:
    by_pattern[r["pattern_id"]].append(r)

print(f"\n{'Pattern':<10} {'Count':>5} {'Compile':>8} {'Correct':>8} {'Avg Spd O0':>12} {'Avg Spd O3':>12}")
print("-" * 60)
for pid in sorted(by_pattern.keys()):
    rows = by_pattern[pid]
    n = len(rows)
    comp = sum(1 for r in rows if r["compiles_O0"])
    corr = sum(1 for r in rows if r["correct_O0"])
    avg_o0 = sum(r["speedup_O0"] for r in rows if r["correct_O0"]) / max(corr, 1)
    avg_o3 = sum(r["speedup_O3"] for r in rows if r["correct_O3"]) / max(corr, 1)
    print(f"{pid:<10} {n:>5} {comp:>8} {corr:>8} {avg_o0:>11.1f}x {avg_o3:>11.1f}x")

if errors:
    print(f"\n{len(errors)} errors:")
    for e in errors[:10]:
        print(f"  {e}")
