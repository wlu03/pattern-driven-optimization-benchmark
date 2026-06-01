"""modal_app/inference.py — fan-out inference over the benchmark dataset.

Runs every active dataset variant through one open-source model served by
vLLM on Modal, writes results to a CSV that scripts/transfer_analysis.py
and faithfulness/report_2x2.py can consume directly.

Usage (from your laptop, with Modal CLI installed and `modal token set`):

    modal run modal_app/inference.py::evaluate_all \
        --model qwen2.5-coder-7b-instruct \
        --strategy taxonomy-guided \
        --output results/qwen25_coder_7b_taxonomy.csv

Models pre-wired (see MODELS dict below): the Pareto-frontier shortlist.
Add new entries to the dict to evaluate more.

GPU pinning per model size:
    1.5B-3B  -> T4   ($0.59/hr)
    7B       -> A10G ($1.10/hr)
    14B      -> L40S ($1.95/hr)
    32B      -> A100-80GB ($2.50/hr)
    70B+     -> H100 ($3.95/hr) or H200

Typical wall-clock for 1,244 variants with 10 concurrent containers:
    7B   on 10x A10G: ~6 min,  ~$1.10 (10 containers x 0.1h x $1.10)
    32B  on 10x A100: ~15 min, ~$6
    70B  on  4x H100: ~25 min, ~$6.50
"""
import json
import os
from pathlib import Path

import modal

APP_NAME = "pdob-inference"

# --- Pareto-frontier shortlist ------------------------------------------------
# Model recipes — pick by string key on the CLI via --model
MODELS = {
    "qwen2.5-coder-1.5b": {
        "hf_id": "Qwen/Qwen2.5-Coder-1.5B-Instruct",
        "gpu":   "T4",
        "max_model_len": 8192,
    },
    "qwen2.5-coder-7b": {
        "hf_id": "Qwen/Qwen2.5-Coder-7B-Instruct",
        "gpu":   "A10G",
        "max_model_len": 8192,
    },
    "qwen2.5-coder-14b": {
        "hf_id": "Qwen/Qwen2.5-Coder-14B-Instruct",
        "gpu":   "L40S",
        "max_model_len": 8192,
    },
    "qwen2.5-coder-32b": {
        "hf_id": "Qwen/Qwen2.5-Coder-32B-Instruct",
        "gpu":   "A100-80GB",
        "max_model_len": 8192,
    },
    "deepseek-r1-distill-qwen-1.5b": {
        "hf_id": "deepseek-ai/DeepSeek-R1-Distill-Qwen-1.5B",
        "gpu":   "T4",
        "max_model_len": 8192,
    },
    "deepseek-r1-distill-qwen-7b": {
        "hf_id": "deepseek-ai/DeepSeek-R1-Distill-Qwen-7B",
        "gpu":   "A10G",
        "max_model_len": 8192,
    },
    "deepseek-r1-distill-qwen-32b": {
        "hf_id": "deepseek-ai/DeepSeek-R1-Distill-Qwen-32B",
        "gpu":   "A100-80GB",
        "max_model_len": 8192,
    },
    "codestral-22b": {
        "hf_id": "mistralai/Codestral-22B-v0.1",
        "gpu":   "L40S",
        "max_model_len": 8192,
    },
    "llama-3.3-70b": {
        "hf_id": "meta-llama/Llama-3.3-70B-Instruct",
        "gpu":   "H100",
        "max_model_len": 8192,
    },
}

# --- Modal app + image -------------------------------------------------------
app = modal.App(APP_NAME)

vllm_image = (
    modal.Image.from_registry(
        "nvidia/cuda:12.9.0-devel-ubuntu22.04", add_python="3.12"
    )
    .entrypoint([])
    .uv_pip_install(
        "vllm==0.21.0",
        "huggingface_hub[hf_transfer]==0.26.0",
    )
    .env({"HF_HUB_ENABLE_HF_TRANSFER": "1"})
)

# Persistent volumes for HF + vLLM cache so models don't re-download per run
hf_cache_vol  = modal.Volume.from_name("pdob-hf-cache", create_if_missing=True)
vllm_cache_vol = modal.Volume.from_name("pdob-vllm-cache", create_if_missing=True)

VOLUMES = {
    "/root/.cache/huggingface": hf_cache_vol,
    "/root/.cache/vllm":        vllm_cache_vol,
}


# --- Inference function ------------------------------------------------------
@app.cls(
    image=vllm_image,
    volumes=VOLUMES,
    timeout=60 * 60,                  # 1 h max per container
    scaledown_window=5 * 60,          # keep warm 5 min after last call
)
class VLLMServer:
    model_key: str = modal.parameter()

    @modal.enter()
    def load(self):
        """One-time model load per container."""
        from vllm import LLM
        cfg = MODELS[self.model_key]
        self.llm = LLM(
            model=cfg["hf_id"],
            max_model_len=cfg["max_model_len"],
            trust_remote_code=True,
            dtype="auto",
        )
        # vLLM auto-loads sampling params from generation_config.json; we
        # override below for deterministic-ish optimization output.

    @modal.method()
    def generate_one(self, prompt: str, max_tokens: int = 2048) -> str:
        """Run one prompt; return raw model text."""
        from vllm import SamplingParams
        params = SamplingParams(
            temperature=0.0,
            top_p=1.0,
            max_tokens=max_tokens,
        )
        out = self.llm.generate([prompt], params)[0]
        return out.outputs[0].text


# --- Local entrypoint --------------------------------------------------------
def _load_active_variants(dataset_dir: str) -> list[dict]:
    """Load variant metadata + slow.c source for every active variant."""
    variants = []
    for md_path in Path(dataset_dir).rglob("metadata.json"):
        if "excluded" in md_path.parts:
            continue
        try:
            meta = json.loads(md_path.read_text())
        except Exception:
            continue
        slow_c = md_path.parent / "slow.c"
        if not slow_c.exists():
            continue
        meta["_variant_dir"] = str(md_path.parent)
        meta["_slow_src"]    = slow_c.read_text()
        variants.append(meta)
    return variants


def _build_prompt(slow_src: str, strategy: str, pattern_meta: dict) -> str:
    """Pull the prompt builder from pdob_core so this stays consistent
    with scripts/evaluate.py."""
    import sys
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
    from pdob_core.prompts import build_prompt
    return build_prompt(slow_src, strategy, pattern_meta)


@app.local_entrypoint()
def evaluate_all(
    model: str,
    strategy: str = "taxonomy-guided",
    output: str = "results.csv",
    dataset_dir: str = "dataset",
    limit: int = 0,
    max_concurrent: int = 10,
):
    """Fan out inference across the active dataset.

    Args:
        model: key in MODELS dict (run with --help to list)
        strategy: prompt strategy (generic | pattern-aware | taxonomy-guided | ...)
        output: CSV path for results
        dataset_dir: where to find variants
        limit: 0 for full sweep; >0 for a smoke test
        max_concurrent: vLLM container count (cost scales linearly)
    """
    import csv
    if model not in MODELS:
        raise SystemExit(f"Unknown model {model!r}. "
                         f"Available: {list(MODELS)}")
    variants = _load_active_variants(dataset_dir)
    if limit > 0:
        variants = variants[:limit]
    print(f"Loaded {len(variants)} active variants")

    server = VLLMServer.with_options(
        gpu=MODELS[model]["gpu"],
        max_containers=max_concurrent,
    )(model_key=model)

    prompts = [_build_prompt(v["_slow_src"], strategy, v) for v in variants]
    print(f"Submitting {len(prompts)} prompts to {model} on "
          f"{MODELS[model]['gpu']} (max {max_concurrent} parallel)...")

    # .map() auto-batches across containers
    results = list(server.generate_one.map(prompts, order_outputs=True))

    out_path = Path(output)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with open(out_path, "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["variant_id", "pattern_id", "model", "strategy",
                    "raw_output_chars", "raw_output"])
        for v, r in zip(variants, results):
            w.writerow([v["variant_id"], v["pattern_id"], model, strategy,
                        len(r), r])
    print(f"Wrote {len(results)} results to {out_path}")
    print(f"Next: python3 scripts/evaluate.py --score-from-csv {out_path}")
