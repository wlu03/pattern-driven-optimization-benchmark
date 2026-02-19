#!/usr/bin/env python3
"""Compile and test a single generated variant."""
import sys, os, subprocess, tempfile, json

if len(sys.argv) < 2:
    print("Usage: python3 test_variant.py <variant_dir>")
    sys.exit(1)

d = sys.argv[1]
slow = open(os.path.join(d, "slow.c")).read()
fast = open(os.path.join(d, "fast.c")).read()
test = open(os.path.join(d, "test.c")).read()

full = test.replace("// SLOW_CODE_HERE", slow).replace("// FAST_CODE_HERE", fast)

with tempfile.TemporaryDirectory() as tmp:
    src = os.path.join(tmp, "test.c")
    with open(src, "w") as f:
        f.write(full)

    for opt in ["-O0", "-O3"]:
        bin_path = os.path.join(tmp, f"test{opt}")
        r = subprocess.run(["gcc", opt, "-o", bin_path, src, "-lm"],
                           capture_output=True, text=True, timeout=10)
        if r.returncode != 0:
            print(f"[COMPILE {opt}] FAIL: {r.stderr[:200]}")
            continue
        print(f"[COMPILE {opt}] OK")

        r = subprocess.run([bin_path], capture_output=True, text=True, timeout=30)
        if r.returncode == 0:
            print(f"[RUN {opt}] {r.stdout.strip()}")
        else:
            print(f"[RUN {opt}] ERROR: {r.stderr[:200]}")

meta = json.load(open(os.path.join(d, "metadata.json")))
print(f"[META] {meta['variant_id']}: {meta['variant_desc']} (difficulty={meta['difficulty']})")
