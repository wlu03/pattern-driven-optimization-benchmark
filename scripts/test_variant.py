#!/usr/bin/env python3
"""Compile and test a single generated variant.

Mirrors the multi-translation-unit compile path used by ``batch_test.py``:
``slow.c``, ``fast.c``, ``test.c``, and ``helper.c`` (when present) are
compiled as separate TUs with ``-fno-lto`` so the compiler cannot inline
the inefficiency across file boundaries.
"""
import json
import os
import subprocess
import sys
import tempfile

# Reuse the extern-declaration extractor from batch_test.py so test.c
# does not see the function bodies at compile time.
_SCRIPTS_DIR = os.path.dirname(os.path.abspath(__file__))
if _SCRIPTS_DIR not in sys.path:
    sys.path.insert(0, _SCRIPTS_DIR)
from batch_test import extract_extern_decl  # noqa: E402

_C_HEADERS = ("#include <stdio.h>\n#include <stdlib.h>\n"
              "#include <math.h>\n#include <string.h>\n\n")


def main() -> int:
    if len(sys.argv) < 2:
        print("Usage: python3 test_variant.py <variant_dir>")
        return 1

    variant_dir = sys.argv[1]
    slow = open(os.path.join(variant_dir, "slow.c")).read()
    fast = open(os.path.join(variant_dir, "fast.c")).read()
    test = open(os.path.join(variant_dir, "test.c")).read()
    helper_path = os.path.join(variant_dir, "helper.c")

    slow_decl = extract_extern_decl(slow)
    fast_decl = extract_extern_decl(fast)
    test_with_decls = (test
        .replace("// SLOW_CODE_HERE", slow_decl)
        .replace("// FAST_CODE_HERE", fast_decl))

    with tempfile.TemporaryDirectory() as tmp:
        slow_src = os.path.join(tmp, "slow.c")
        fast_src = os.path.join(tmp, "fast.c")
        test_src = os.path.join(tmp, "test.c")

        with open(slow_src, "w") as f:
            f.write((_C_HEADERS if "#include" not in slow else "") + slow)
        with open(fast_src, "w") as f:
            f.write((_C_HEADERS if "#include" not in fast else "") + fast)
        with open(test_src, "w") as f:
            f.write(test_with_decls)

        extra_tus = [helper_path] if os.path.exists(helper_path) else []

        for opt in ["-O0", "-O3"]:
            bin_path = os.path.join(tmp, f"test{opt}")
            r = subprocess.run(
                ["gcc", opt, "-fno-lto", "-o", bin_path,
                 test_src, slow_src, fast_src] + extra_tus + ["-lm"],
                capture_output=True, text=True, timeout=30)
            if r.returncode != 0:
                print(f"[COMPILE {opt}] FAIL: {r.stderr[:200]}")
                continue
            print(f"[COMPILE {opt}] OK")

            r = subprocess.run([bin_path], capture_output=True, text=True, timeout=60)
            if r.returncode == 0:
                print(f"[RUN {opt}] {r.stdout.strip()}")
            else:
                print(f"[RUN {opt}] ERROR: {r.stderr[:200]}")

    meta = json.load(open(os.path.join(variant_dir, "metadata.json")))
    print(f"[META] {meta['variant_id']}: {meta['variant_desc']} "
          f"(difficulty={meta['difficulty']})")
    return 0


if __name__ == "__main__":
    sys.exit(main())
