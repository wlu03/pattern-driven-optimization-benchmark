"""modal_app/score_modal.py — run scoring (compile + correctness + speedup +
faithfulness) on Modal CPU containers instead of locally.

Why: local scoring is slow (per-candidate gcc + run + watchdog timeouts on broken
code) AND local background processes get killed between turns. Modal containers
survive (--detach), parallelize (one per cell), and are x86 Linux — so the x86
intrinsics (crc32/SSE) that fail to compile on Apple-Silicon arm64 compile here.

Each call scores one completions CSV against the baked-in dataset and writes
<name>_scored.csv to the `pdob-results` volume. Spawn many in parallel; pull
results with `modal volume get pdob-results`.

Usage:
    modal run modal_app/score_modal.py --glob 'results/pareto_ft_indist/*-ft_pattern-aware.csv'
    modal volume get pdob-results <name>_scored.csv ./results/pareto_ft_indist/
"""
import glob
from pathlib import Path

import modal

app = modal.App("pdob-score")

# Bake the repo code + dataset into the image so scoring needs no local mount at
# runtime (survives detached). x86 gcc + pycparser is all the scorer needs.
score_image = (
    modal.Image.debian_slim(python_version="3.12")
    .apt_install("build-essential")
    .pip_install("pycparser")
    .add_local_dir("pdob_core", "/root/pdob_core", copy=True)
    .add_local_dir("faithfulness", "/root/faithfulness", copy=True)
    .add_local_dir("scripts", "/root/scripts", copy=True)
    .add_local_dir("dataset", "/root/dataset", copy=True)
)
results_vol = modal.Volume.from_name("pdob-results", create_if_missing=True)


@app.function(image=score_image, cpu=4.0, timeout=3 * 60 * 60,
              volumes={"/results": results_vol})
def score_cell(name: str, completions_bytes: bytes, strategy: str,
               runs: int = 1, faithfulness: bool = True,
               compile_timeout: int = 10, run_timeout: int = 15) -> str:
    """Score one completions CSV on Modal; write /results/<name>_scored.csv.

    Output is NOT captured — it streams to the container stdout so `modal app
    logs <id>` shows live per-candidate progress. faithfulness=False skips the
    9-config differential execution (much faster; enough for pass@1 crossover).
    """
    import os
    import subprocess
    os.chdir("/root")
    Path("/tmp/in.csv").write_bytes(completions_bytes)
    out = f"/results/{name}_scored.csv"
    # Shorter compile/run timeouts than the local default (broken candidates die
    # fast); x86 so intrinsics compile.
    env = dict(os.environ, PDOB_COMPILE_TIMEOUT=str(compile_timeout),
               PDOB_RUN_TIMEOUT=str(run_timeout))
    cmd = ["python", "-u", "scripts/score_completions.py", "/tmp/in.csv",
           "--strategy", strategy, "--output", out, "--runs", str(runs)]
    if faithfulness:
        cmd.append("--faithfulness")
    print(f"[{name}] START faithfulness={faithfulness} runs={runs}", flush=True)
    r = subprocess.run(cmd, env=env)   # inherit stdout/stderr -> Modal logs
    results_vol.commit()
    print(f"[{name}] DONE rc={r.returncode}", flush=True)
    return f"{name}:{r.returncode}"


@app.local_entrypoint()
def main(glob_pattern: str, strategy: str = "pattern-aware", runs: int = 1,
         faithfulness: bool = True):
    files = [f for f in sorted(glob.glob(glob_pattern)) if not f.endswith("_scored.csv")]
    if not files:
        raise SystemExit(f"no files matched {glob_pattern!r}")
    print(f"Scoring {len(files)} cells on Modal (parallel, faithfulness={faithfulness}):")
    handles = []
    for f in files:
        name = Path(f).name[:-4]  # strip .csv
        print(f"  {name}")
        handles.append((name, score_cell.spawn(
            name, Path(f).read_bytes(), strategy, runs, faithfulness)))
    for name, h in handles:
        print(f"  ✓ {h.get()}")
    print("\nPull results:\n  modal volume get pdob-results <name>_scored.csv ./results/...")
