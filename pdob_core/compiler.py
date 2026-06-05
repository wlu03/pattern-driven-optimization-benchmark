import os
import re
import subprocess
import tempfile
import time

# --- Resource caps for executing untrusted, LLM-generated binaries -------
# macOS does NOT enforce RLIMIT_AS / `ulimit -v`, so a generated binary with
# a bad allocation can exhaust all RAM and crash the machine before its
# wall-clock timeout fires. We instead run each binary under a watchdog that
# polls resident memory (via `ps`, since psutil isn't a dep and macOS has no
# /proc) and caps captured output, killing the child if it exceeds either.
# A killed binary is reported as a runtime error -- the correct outcome for a
# broken optimization. Real benchmarks here allocate a few hundred MB at most
# (largest is ~10M doubles = 80 MB/array), so these caps never trip on
# legitimate code; they only catch pathological allocations / print loops.
MEM_CAP_MB = int(os.environ.get("PDOB_MEM_CAP_MB", "4096"))   # per-process RSS
OUT_CAP_MB = int(os.environ.get("PDOB_OUT_CAP_MB", "64"))     # captured stdout
_RSS_CAP_KB = MEM_CAP_MB * 1024
_OUT_CAP_BYTES = OUT_CAP_MB * 1024 * 1024


def _rss_kb(pid):
    """Resident set size of ``pid`` in KB, or None if it can't be read."""
    try:
        out = subprocess.run(
            ["ps", "-o", "rss=", "-p", str(pid)],
            capture_output=True, text=True, timeout=5,
        ).stdout.strip()
        return int(out) if out else None
    except Exception:
        return None


def _run_with_limits(cmd, timeout, env, poll=0.1):
    """Run ``cmd`` under a wall-clock, resident-memory, and output watchdog.

    Returns ``(returncode, stdout, stderr, reason)`` where ``reason`` is
    None on a clean exit, or one of ``"timeout" | "memory" | "output"`` if
    the watchdog killed the child. stdout/stderr are written to temp files
    (not PIPEs) so a runaway print loop can't balloon the parent's memory.
    """
    with tempfile.TemporaryFile() as out_f, tempfile.TemporaryFile() as err_f:
        proc = subprocess.Popen(cmd, stdout=out_f, stderr=err_f, env=env)
        start = time.monotonic()
        reason = None
        while True:
            try:
                proc.wait(timeout=poll)
                break  # exited on its own
            except subprocess.TimeoutExpired:
                pass   # still running -- check the caps
            if time.monotonic() - start > timeout:
                reason = "timeout"
                break
            rss = _rss_kb(proc.pid)
            if rss is not None and rss > _RSS_CAP_KB:
                reason = "memory"
                break
            if out_f.tell() > _OUT_CAP_BYTES:
                reason = "output"
                break
        if reason:
            proc.kill()
            try:
                proc.wait(timeout=5)
            except Exception:
                pass
        out_f.seek(0)
        stdout = out_f.read(_OUT_CAP_BYTES + 1).decode("utf-8", "replace")
        err_f.seek(0)
        stderr = err_f.read(65536).decode("utf-8", "replace")
    return proc.returncode, stdout, stderr, reason


def compile_and_run(code: str, test_harness: str, timeout: int = 120,
                    opt_level: str = "O2", runs: int = 3,
                    compile_timeout: int = 30, compiler: str = "gcc",
                    env: dict = None) -> dict:
    """Compile LLM-generated code with test harness, run, parse output.

    Compiles at opt_level (default O2) and takes the median of `runs`
    executions for stable timing.

    Parameters
    ----------
    env : dict, optional
        Extra environment variables passed to the compiled binary.  When
        ``None`` (the default) the subprocess inherits the parent's
        environment exactly — preserves backward compatibility with all
        existing callers.  Used by ``scripts/run_multi_input.py`` to set
        ``BENCH_N`` / ``BENCH_SEED`` / ``BENCH_DIST`` and re-run the same
        compiled harness under different input configurations.
    """
    with tempfile.TemporaryDirectory() as tmpdir:
        src_path = os.path.join(tmpdir, "test.c")
        bin_path = os.path.join(tmpdir, "test")

        full_code = test_harness.replace("// LLM_CODE_HERE", code)
        with open(src_path, "w") as f:
            f.write(full_code)

        result = subprocess.run(
            [compiler, f"-{opt_level}", "-o", bin_path, src_path, "-lm"],
            capture_output=True, text=True, timeout=compile_timeout
        )
        if result.returncode != 0:
            return {"compiles": False, "error": result.stderr}

        times = []
        correct = False
        result_val = ""
        for _ in range(runs):
            rc, stdout, _stderr, reason = _run_with_limits(
                [bin_path], timeout, env,
            )
            if reason == "timeout":
                # Preserve the original subprocess.run(timeout=) contract:
                # callers already expect TimeoutExpired to propagate.
                raise subprocess.TimeoutExpired([bin_path], timeout)
            if reason in ("memory", "output") or rc != 0:
                detail = reason or f"exit {rc}"
                return {"compiles": True, "correct": False,
                        "error": f"runtime error ({detail})"}
            output = stdout.strip()
            parts = dict(p.split("=") for p in output.split() if "=" in p)
            correct = parts.get("correct", "0") == "1"
            result_val = parts.get("result", "")
            t = float(parts.get("time_ms", 0))
            if t > 0:
                times.append(t)

        times.sort()
        time_ms = times[len(times) // 2] if times else 0.0
        # MAD = median(|x - median(x)|). Robust spread of the per-run timings,
        # useful for downstream stability reporting.
        if times:
            mad_ms = sorted(abs(t - time_ms) for t in times)[len(times) // 2]
        else:
            mad_ms = 0.0

        return {
            "compiles": True,
            "correct": correct,
            "time_ms": time_ms,
            "time_ms_mad": mad_ms,
            "time_ms_runs": list(times),
            "result": result_val,
        }


def _optimized_call_arity(test_harness: str):
    """Return the arg-count of the `optimized(...)` call in test_harness, or None."""
    if not test_harness:
        return None
    m = re.search(r'\boptimized\s*\(([^;{}]*?)\)\s*;', test_harness)
    if not m:
        return None
    inner = m.group(1).strip()
    if not inner:
        return 0
    depth = 0
    n = 1
    for ch in inner:
        if ch == '(':
            depth += 1
        elif ch == ')':
            depth -= 1
        elif ch == ',' and depth == 0:
            n += 1
    return n


def normalize_function_name(code: str, test_harness: str = None) -> str:
    """Rename the public entry-point C function to `optimized`.

    Strategy:
      1. If `optimized` already exists in `code`, leave everything alone.
      2. If `test_harness` is supplied, pick the function whose parameter
         count matches the `optimized(...)` call site in the harness. This
         is the only correct disambiguator for patterns whose harness calls
         multiple functions defined in `code` (e.g. DS-1 expects both
         `ds1_build_ht` and `optimized`).
      3. Otherwise fall back to the most-parameters heuristic with ties
         broken by position (later wins). Entry points typically take
         arrays + sizes; helpers take scalar values.
    """
    if re.search(r'\b(?:int|void|float|double|char|long|short|unsigned|signed|size_t)\s+optimized\s*\(', code):
        return code

    target_arity = _optimized_call_arity(test_harness)

    def _pick(cands):
        # cands: list of (name, n_params, position)
        if not cands:
            return None
        if target_arity is not None:
            matching = [c for c in cands if c[1] == target_arity]
            if matching:
                return max(matching, key=lambda c: c[2])
        return max(cands, key=lambda c: (c[1], c[2]))

    try:
        from pycparser import CParser, c_ast
        stripped = re.sub(r'^\s*#.*$', '', code, flags=re.MULTILINE)
        stripped = re.sub(r'__attribute__\s*\(\([^)]*\)\)', '', stripped)
        ast = CParser().parse(stripped, filename='<llm>')
        candidates = []
        for pos, node in enumerate(ast.ext):
            if isinstance(node, c_ast.FuncDef):
                storage = node.decl.storage or []
                if 'static' in storage:
                    continue
                if node.decl.name == 'optimized':
                    return code
                params = node.decl.type.args
                n_params = len(params.params) if params else 0
                candidates.append((node.decl.name, n_params, pos))
        best = _pick(candidates)
        if best:
            return re.sub(r'\b' + re.escape(best[0]) + r'\b', 'optimized', code)
    except Exception:
        pass

    pattern = re.compile(
        r'(?:^|\n)\s*(?!static\b)(?:[A-Za-z_]\w*[\s\*]+)+([A-Za-z_]\w*)\s*\(([^)]*)\)\s*\{',
        re.MULTILINE,
    )
    keywords = {'if', 'for', 'while', 'switch', 'return', 'sizeof', 'do', 'else'}
    candidates = []
    for pos, m in enumerate(pattern.finditer(code)):
        name = m.group(1)
        if name in keywords:
            continue
        if name == 'optimized':
            return code
        params_str = m.group(2).strip()
        n_params = 0 if not params_str or params_str.lower() == 'void' \
                     else len([p for p in params_str.split(',') if p.strip()])
        candidates.append((name, n_params, pos))
    best = _pick(candidates)
    if best:
        return re.sub(r'\b' + re.escape(best[0]) + r'\b', 'optimized', code)
    return code


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


def extract_code_from_response(response: str, test_harness: str = None) -> str:
    """Extract C code from an LLM markdown response.

    Prefers ```c-labeled blocks, falls back to any fenced block, then to
    the whole response. Among candidates, picks the longest. Tolerates
    unterminated fences by treating the rest of the response as the body.
    When test_harness is supplied, the entry-point rename uses the
    arg-count of the `optimized(...)` call site for disambiguation.
    """
    c_blocks = re.findall(r"```c\s*(.*?)```", response, flags=re.DOTALL)
    if c_blocks:
        code = max(c_blocks, key=len).strip()
    else:
        any_blocks = re.findall(r"```\w*\s*(.*?)```", response, flags=re.DOTALL)
        if any_blocks:
            code = max(any_blocks, key=len).strip()
        else:
            unterminated = re.search(r"```(?:c)?\s*(.*)", response, flags=re.DOTALL)
            code = unterminated.group(1).strip() if unterminated else response.strip()
    return normalize_function_name(code, test_harness)
