import os
import re
import subprocess
import tempfile


def compile_and_run(code: str, test_harness: str, timeout: int = 120,
                    opt_level: str = "O2", runs: int = 3) -> dict:
    """Compile LLM-generated code with test harness, run, parse output.

    Compiles at opt_level (default O2) and takes the median of `runs`
    executions for stable timing.
    """
    with tempfile.TemporaryDirectory() as tmpdir:
        src_path = os.path.join(tmpdir, "test.c")
        bin_path = os.path.join(tmpdir, "test")

        full_code = test_harness.replace("// LLM_CODE_HERE", code)
        with open(src_path, "w") as f:
            f.write(full_code)

        result = subprocess.run(
            ["gcc", f"-{opt_level}", "-o", bin_path, src_path, "-lm"],
            capture_output=True, text=True, timeout=10
        )
        if result.returncode != 0:
            return {"compiles": False, "error": result.stderr}

        times = []
        correct = False
        result_val = ""
        for _ in range(runs):
            run = subprocess.run(
                [bin_path], capture_output=True, text=True, timeout=timeout
            )
            if run.returncode != 0:
                return {"compiles": True, "correct": False, "error": "runtime error"}
            output = run.stdout.strip()
            parts = dict(p.split("=") for p in output.split() if "=" in p)
            correct = parts.get("correct", "0") == "1"
            result_val = parts.get("result", "")
            t = float(parts.get("time_ms", 0))
            if t > 0:
                times.append(t)

        times.sort()
        time_ms = times[len(times) // 2] if times else 0.0

        return {
            "compiles": True,
            "correct": correct,
            "time_ms": time_ms,
            "result": result_val,
        }


def normalize_function_name(code: str) -> str:
    """Rename the last defined C function to `optimized`.

    Models often ignore the rename instruction and use names like
    `sr1_optimized`, `sr1_fast`, or `optimized_sr1`. This finds the
    last function definition in the code and renames it (and all calls
    to it) to `optimized`, which is what the test harnesses expect.
    """
    pattern = re.compile(
        r'\b([A-Za-z_]\w*)\s*\('
        r'[^)]*\)\s*\{',
        re.MULTILINE,
    )
    matches = list(pattern.finditer(code))
    if not matches:
        return code

    func_name = None
    for m in reversed(matches):
        name = m.group(1)
        if name in ("if", "for", "while", "switch", "return"):
            continue
        func_name = name
        break

    if func_name is None or func_name == "optimized":
        return code

    return re.sub(r'\b' + re.escape(func_name) + r'\b', 'optimized', code)


def sanitize_llm_code(code: str, test_harness: str) -> str:
    """Strip typedef/struct/enum re-definitions from LLM code that would
    conflict with types already pre-defined in the test harness.

    Also strips x86-specific SIMD headers (immintrin.h, xmmintrin.h, etc.)
    that won't compile on non-x86 hosts (e.g. Apple Silicon arm64).
    """
    x86_simd_headers = [
        "immintrin.h", "xmmintrin.h", "emmintrin.h", "pmmintrin.h",
        "tmmintrin.h", "smmintrin.h", "nmmintrin.h", "avxintrin.h",
        "avx2intrin.h", "avx512fintrin.h",
    ]
    for hdr in x86_simd_headers:
        code = re.sub(
            r'#\s*include\s*[<"]' + re.escape(hdr) + r'[>"]\s*\n?',
            '', code
        )

    before_llm = test_harness.split("// LLM_CODE_HERE")[0]
    pre_names = set(re.findall(
        r'typedef\s+(?:struct|enum)\s*(?:\w+\s*)?\{[^}]*\}\s*(\w+)\s*;',
        before_llm, re.DOTALL
    ))

    for name in pre_names:
        code = re.sub(
            r'typedef\s+struct\s*(?:\w+\s*)?\{[^}]*\}\s*' + re.escape(name) + r'\s*;',
            '', code, flags=re.DOTALL
        )
        code = re.sub(
            r'typedef\s+enum\s*(?:\w+\s*)?\{[^}]*\}\s*' + re.escape(name) + r'\s*;',
            '', code, flags=re.DOTALL
        )

    return code.strip()


def extract_code_from_response(response: str) -> str:
    """Extract C code from an LLM markdown response."""
    if "```c" in response:
        start = response.index("```c") + 4
        end = response.index("```", start)
        code = response[start:end].strip()
    elif "```" in response:
        start = response.index("```") + 3
        end = response.index("```", start)
        code = response[start:end].strip()
    else:
        code = response.strip()
    return normalize_function_name(code)
