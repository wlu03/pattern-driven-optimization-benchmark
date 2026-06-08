"""modal_app/inference.py — fan-out inference over the benchmark dataset.

Runs every active dataset variant through one open-source model served by
vLLM on Modal, writes results to a CSV that scripts/transfer_analysis.py
and faithfulness/report_2x2.py can consume directly.

Usage (from your laptop, with Modal CLI installed and `modal token new`):

    modal run modal_app/inference.py::evaluate_all \
        --model qwen2.5-coder-7b \
        --strategy taxonomy-guided \
        --output results/qwen25_coder_7b_taxonomy.csv

Models pre-wired (see MODELS dict below): the Pareto-frontier shortlist.

GPU pinning per model size:
    1.5B-3B  -> T4   ($0.59/hr)
    7B       -> A10G ($1.10/hr)
    14B      -> L40S ($1.95/hr)
    32B      -> A100-80GB ($2.50/hr)
    70B+     -> H100 ($3.95/hr)

Typical wall-clock for 1,244 variants with 10 concurrent containers:
    7B   on 10x A10G:  ~6 min,  ~$1.10
    32B  on 10x A100:  ~15 min, ~$6
    70B  on  4x H100:  ~25 min, ~$6.50
"""
import json
import sys
from pathlib import Path

import modal

APP_NAME = "pdob-inference"
REPO_ROOT = Path(__file__).resolve().parents[1]

# --- Pareto-frontier shortlist ----------------------------------------------
# Per-model config. `reasoning` flag = the model emits a separate <think>
# trace before its answer. When True, the harness asks vLLM to expose
# `reasoning_content` (via --enable-reasoning + --reasoning-parser deepseek_r1
# in vLLM's CLI; we pass equivalent kwargs to LLM()). The trace is recorded
# in the CSV's raw_reasoning column for scripts/cot_alignment_analysis.py,
# NOT used as a verdict input (see docs/implementation.tex on why).
MODELS = {
    "qwen2.5-coder-1.5b": {
        "hf_id": "Qwen/Qwen2.5-Coder-1.5B-Instruct",
        "gpu":   "T4",
        "max_model_len": 4096,   # T4 has 16 GB — keep KV cache modest
        "reasoning": False,
    },
    "qwen2.5-coder-7b": {
        "hf_id": "Qwen/Qwen2.5-Coder-7B-Instruct",
        "gpu":   "A10G",
        "max_model_len": 8192,
        "reasoning": False,
    },
    "qwen2.5-coder-14b": {
        "hf_id": "Qwen/Qwen2.5-Coder-14B-Instruct",
        "gpu":   "L40S",
        "max_model_len": 8192,
        "reasoning": False,
    },
    "qwen2.5-coder-32b": {
        "hf_id": "Qwen/Qwen2.5-Coder-32B-Instruct",
        "gpu":   "A100-80GB",
        "max_model_len": 8192,
        "reasoning": False,
    },
    "deepseek-r1-distill-qwen-1.5b": {
        "hf_id": "deepseek-ai/DeepSeek-R1-Distill-Qwen-1.5B",
        "gpu":   "T4",
        "max_model_len": 4096,   # T4 has 16 GB — keep KV cache modest
        "reasoning": True,
        "reasoning_parser": "deepseek_r1",
    },
    "deepseek-r1-distill-qwen-7b": {
        "hf_id": "deepseek-ai/DeepSeek-R1-Distill-Qwen-7B",
        "gpu":   "A10G",
        "max_model_len": 8192,
        "reasoning": True,
        "reasoning_parser": "deepseek_r1",
    },
    "deepseek-r1-distill-qwen-32b": {
        "hf_id": "deepseek-ai/DeepSeek-R1-Distill-Qwen-32B",
        "gpu":   "A100-80GB",
        "max_model_len": 8192,
        "reasoning": True,
        "reasoning_parser": "deepseek_r1",
    },
    "codestral-22b": {
        "hf_id": "mistralai/Codestral-22B-v0.1",
        # L40S (48 GB) OOMs during KV-cache allocation:
        # `Available KV cache memory: -4.85 GiB` (22B bf16 weights ≈ 44 GB
        # plus workspace exceeds 0.85 * 48 GB allocation). Move to
        # A100-80GB so KV cache has room. Cost delta: $1.95/hr → $2.50/hr.
        "gpu":   "A100-80GB",
        "max_model_len": 8192,
        "reasoning": False,
    },
    # DeepSeek-R1-Distill-Llama-70B — non-gated (MIT) reasoning distill; the
    # 70B member of the DeepSeek-R1-Distill series (base: Llama-3.3-70B). Used
    # in place of the gated meta-llama/Llama-3.3-70B-Instruct so no HF token is
    # needed. 70B bf16 checkpoint ≈ 131 GiB — a single H200 (140 GiB) loads the
    # weights but has no room left for the KV cache ("Available KV cache: -16
    # GiB"), so shard across 2× H200 with tensor parallelism.
    "deepseek-r1-distill-llama-70b": {
        "hf_id": "deepseek-ai/DeepSeek-R1-Distill-Llama-70B",
        "gpu":   "H200:2",
        "tensor_parallel_size": 2,
        "max_model_len": 8192,
        "reasoning": True,
        "reasoning_parser": "deepseek_r1",
    },
    # Non-gated 72B-class general-purpose model. 72B bf16 checkpoint ≈ 135 GiB —
    # does NOT fit one H200 (140 GiB) once memory profiling + KV cache are added
    # (OOMs with ~131 MiB free). Shard across 2× H200 with tensor parallelism.
    "qwen2.5-72b": {
        "hf_id": "Qwen/Qwen2.5-72B-Instruct",
        "gpu":   "H200:2",
        "tensor_parallel_size": 2,
        "max_model_len": 8192,
        "reasoning": False,
    },
    # Codestral may also be gated depending on HF account access policy.
    # If you see "Cannot access gated repo" errors, add "needs_hf_token": True
    # to its entry too.

    # ── Added anchors (non-gated) ─────────────────────────────────────────
    # Second reasoning family + newer generation, both 32B. Both emit <think>,
    # so the deepseek_r1 reasoning parser applies.
    #
    # These run on a SINGLE H200 (not A100-80GB) at 16384 ctx, unlike the
    # R1-distill-32b. A limit-4 smoke test showed QwQ on A100-80GB@8192
    # exhausted its token budget (~5k tokens) mid-reasoning and never emitted
    # code — A100-80GB only leaves ~18.9k tokens of KV pool for a 32B model,
    # so it can't hold a longer context. QwQ's reasoning is far more verbose
    # than the R1 distills, so it needs both more tokens (16384) and the KV
    # headroom of an H200 (~58 GiB free after weights) to batch at that length.
    "qwq-32b": {
        # RL-trained reasoning model (NOT an R1 distill). Apache-2.0.
        # max_tokens 12288 (vs 4096 default): a smoke test showed QwQ's <think>
        # alone exceeds 4096 tokens, truncating before any code. 12288 + a
        # ~2-3k prompt stays within the 16384 max_model_len.
        "hf_id": "Qwen/QwQ-32B",
        "gpu":   "H200",
        "max_model_len": 16384,
        "max_tokens": 12288,
        "reasoning": True,
        "reasoning_parser": "deepseek_r1",
    },
    "qwen3-32b": {
        # Newer generation; thinking mode on by default. Apache-2.0.
        "hf_id": "Qwen/Qwen3-32B",
        "gpu":   "H200",
        "max_model_len": 16384,
        "max_tokens": 12288,
        "reasoning": True,
        "reasoning_parser": "deepseek_r1",
    },
    # Second coder family — tests whether the coder edge is Qwen-specific.
    # Non-reasoning; given comfortable GPU headroom to avoid vLLM-init OOM.
    "opencoder-8b": {
        # Open/reproducible code LLM (infly). ~7B-tier peer to coder-7b.
        "hf_id": "infly/OpenCoder-8B-Instruct",
        "gpu":   "L40S",
        "max_model_len": 8192,
        "reasoning": False,
    },
    "deepseek-coder-v2-lite": {
        # 16B MoE (2.4B active) code model — adds a dense-vs-MoE axis too.
        "hf_id": "deepseek-ai/DeepSeek-Coder-V2-Lite-Instruct",
        "gpu":   "A100-80GB",
        "max_model_len": 8192,
        "reasoning": False,
    },
    "yi-coder-9b": {
        # 9B code model, Apache-2.0. Optional third coder family.
        "hf_id": "01-ai/Yi-Coder-9B-Chat",
        "gpu":   "L40S",
        "max_model_len": 8192,
        "reasoning": False,
    },
}

# Fine-tuned variants produced by modal_app/finetune_weak3.py. Each inherits its
# base model's decode config but loads the merged 16-bit weights from the
# pdob-finetuned volume (mounted at /finetuned, see VOLUMES below). Keep these
# keys in sync with TARGETS[*].name in finetune_weak3.py.
_FINETUNED = {
    "r1-distill-qwen-7b-ft": "deepseek-r1-distill-qwen-7b",
    "yi-coder-9b-ft":        "yi-coder-9b",
    "opencoder-8b-ft":       "opencoder-8b",
}
for _ft_key, _base_key in _FINETUNED.items():
    if _base_key in MODELS:
        MODELS[_ft_key] = {**MODELS[_base_key], "hf_id": f"/finetuned/{_ft_key}"}

# --- Modal app + image ------------------------------------------------------
app = modal.App(APP_NAME)

vllm_image = (
    modal.Image.from_registry(
        "nvidia/cuda:12.9.0-devel-ubuntu22.04", add_python="3.12"
    )
    .entrypoint([])
    .uv_pip_install(
        "vllm==0.21.0",
        # Don't pin huggingface_hub — vllm 0.21.0 requires >=0.34.0 (or >=1.5.0
        # for newer transformers branches); let the resolver pick a compatible
        # version. hf-transfer is enabled via env var below; it's available as
        # a separate `hf_transfer` package or as the `[hf_transfer]` extra of
        # any modern huggingface_hub.
        "hf_transfer",
    )
    .env({"HF_HUB_ENABLE_HF_TRANSFER": "1"})
)

hf_cache_vol   = modal.Volume.from_name("pdob-hf-cache",   create_if_missing=True)
vllm_cache_vol = modal.Volume.from_name("pdob-vllm-cache", create_if_missing=True)
finetuned_vol  = modal.Volume.from_name("pdob-finetuned",  create_if_missing=True)

VOLUMES = {
    "/root/.cache/huggingface": hf_cache_vol,
    "/root/.cache/vllm":        vllm_cache_vol,
    # Merged fine-tuned weights from finetune_weak3.py; *-ft model keys load from here.
    "/finetuned":               finetuned_vol,
}


# --- Inference function -----------------------------------------------------
def _maybe_hf_secret():
    """Return [modal.Secret.from_name("huggingface")] if the secret exists,
    else []. Lets the inference function decorator opt into HF auth without
    hard-failing when the user hasn't set up the secret yet (only the
    gated-model branch actually needs it)."""
    try:
        return [modal.Secret.from_name("huggingface")]
    except Exception:
        return []


@app.cls(
    image=vllm_image,
    volumes=VOLUMES,
    secrets=_maybe_hf_secret(),
    timeout=60 * 60,
    scaledown_window=5 * 60,
)
class VLLMServer:
    model_key: str = modal.parameter()

    @modal.enter()
    def load(self):
        from vllm import LLM
        from transformers import AutoTokenizer
        cfg = MODELS[self.model_key]
        llm_kwargs = dict(
            model=cfg["hf_id"],
            max_model_len=cfg["max_model_len"],
            trust_remote_code=True,
            dtype="auto",
            # Skip CUDA graph compilation — the capture phase OOMs on T4
            # (16 GB) for some model sizes, killing the worker silently.
            # Eager mode is ~10-20% slower at decode but avoids the trap.
            enforce_eager=True,
            # Conservative GPU-mem fraction so KV cache + workspace fits.
            gpu_memory_utilization=0.85,
            # Shard large models across multiple GPUs (1 = single-GPU default).
            # 70B+ bf16 weights exceed a single H200, so those cfgs set this to 2.
            tensor_parallel_size=cfg.get("tensor_parallel_size", 1),
        )
        # Reasoning models: enable vLLM's reasoning-content parser so the
        # <think> trace is exposed separately from the answer text. The
        # answer text alone is what we extract C from; the trace lands
        # in raw_reasoning for cot_alignment_analysis.py.
        self._reasoning_enabled = bool(cfg.get("reasoning"))
        if self._reasoning_enabled:
            llm_kwargs["enable_reasoning"] = True
            llm_kwargs["reasoning_parser"] = cfg.get("reasoning_parser",
                                                      "deepseek_r1")
        try:
            self.llm = LLM(**llm_kwargs)
        except TypeError:
            # Older vLLM may not accept enable_reasoning kwarg. Retry
            # without it (CoT will land in the main text and we'll
            # extract via the <think>...</think> regex in
            # scripts/score_completions.py).
            for k in ("enable_reasoning", "reasoning_parser"):
                llm_kwargs.pop(k, None)
            self.llm = LLM(**llm_kwargs)
            self._reasoning_enabled = False
        # Load the chat-template tokenizer so we can format prompts the
        # way the instruct-tuned model was fine-tuned to expect. Without
        # this, instruct models (Qwen2.5-Coder-Instruct, DeepSeek-R1-
        # Distill-Instruct, Codestral-Instruct, Llama-3.3-70B-Instruct)
        # receive raw text and emit degenerate / empty completions
        # (observed: Qwen2.5-Coder-7B produced empty output for 97% of
        # the 1244 variants on the first sweep because the chat template
        # was not applied).
        self.tokenizer = AutoTokenizer.from_pretrained(
            cfg["hf_id"], trust_remote_code=True,
        )

    @modal.method()
    def generate_batch(self, prompts: list[str],
                       max_tokens: int = 4096) -> list[dict]:
        """Generate completions for a batch.

        Returns a list of {"text": str, "reasoning": Optional[str]} dicts.
        `reasoning` is populated when vLLM's reasoning_content extractor
        is active (output.outputs[0].reasoning_content); None otherwise.
        Downstream score_completions.py will additionally split out
        <think>...</think> blocks from the main text when reasoning was
        not separated by vLLM (fallback for older vLLM versions).
        """
        from vllm import SamplingParams
        # Per-model override: verbose reasoning models (QwQ, Qwen3-thinking)
        # need far more than the 4096 default or they exhaust the budget mid-
        # <think> and never emit code. Set "max_tokens" in their MODELS entry.
        effective_max_tokens = MODELS[self.model_key].get("max_tokens",
                                                           max_tokens)
        params = SamplingParams(
            temperature=0.0, top_p=1.0, max_tokens=effective_max_tokens,
        )
        # Apply each model's chat template so instruct-tuned models get
        # the role/turn markers they were fine-tuned to receive.
        formatted = [
            self.tokenizer.apply_chat_template(
                [{"role": "user", "content": p}],
                tokenize=False,
                add_generation_prompt=True,
            )
            for p in prompts
        ]
        outputs = self.llm.generate(formatted, params)
        results = []
        for o in outputs:
            out0 = o.outputs[0]
            results.append({
                "text":      out0.text,
                "reasoning": getattr(out0, "reasoning_content", None)
                             if self._reasoning_enabled else None,
            })
        return results


# --- Local prompt building (uses pdob_core's authoritative builders) --------
def _build_variant_prompts(variants_meta: list[dict],
                            strategy: str,
                            hw_target: str = "generic") -> list[str]:
    """Use pdob_core's _build_variant_prompt for consistency with the local
    scripts/evaluate.py output. Runs locally on your laptop before submission
    to Modal so we don't have to ship pdob_core into the Modal image."""
    sys.path.insert(0, str(REPO_ROOT))
    from pdob_core.patterns import PATTERNS
    from pdob_core.dataset_evaluator import discover_variants
    from pdob_core.evaluator import _build_variant_prompt

    pattern_lookup = {p.pattern_id: p for p in PATTERNS}
    # Re-map the variant meta dicts back to VariantPaths-like objects
    # (we already loaded them; just give the prompt builder what it needs)
    by_vid = {}
    for v in discover_variants(variants_meta["dataset_dir"]):
        by_vid[v.variant_id] = v

    prompts = []
    for meta in variants_meta["records"]:
        vp = by_vid.get(meta["variant_id"])
        if vp is None:
            raise RuntimeError(f"Variant {meta['variant_id']} not found on disk")
        prompts.append(_build_variant_prompt(vp, pattern_lookup, strategy,
                                              hw_target))
    return prompts


# --- Local entrypoint -------------------------------------------------------
@app.local_entrypoint()
def evaluate_all(
    model: str,
    strategy: str = "taxonomy-guided",
    output: str = "results.csv",
    dataset_dir: str = "dataset",
    limit: int = 0,
    max_concurrent: int = 10,
    hw_target: str = "generic",
):
    """Fan out inference across the active dataset.

    Args:
        model:          key in MODELS dict (run with --help to list)
        strategy:       generic | pattern-aware | taxonomy-guided | hardware-target | diagnosis
        output:         CSV path for results
        dataset_dir:    where to find variants (excluded/ is auto-skipped)
        limit:          0 for full sweep; >0 for a smoke test
        max_concurrent: vLLM container count
        hw_target:      hardware target hint (generic | x86_avx2 | arm_neon | ...)
    """
    import csv
    if model not in MODELS:
        raise SystemExit(f"Unknown model {model!r}. Available: {list(MODELS)}")

    # Build the prompts locally using pdob_core's authoritative builder.
    sys.path.insert(0, str(REPO_ROOT))
    from pdob_core.dataset_evaluator import discover_variants
    from pdob_core.evaluator import _build_variant_prompt
    from pdob_core.patterns import PATTERNS

    variants = list(discover_variants(dataset_dir))
    if limit > 0:
        variants = variants[:limit]
    pattern_lookup = {p.pattern_id: p for p in PATTERNS}

    print(f"Loaded {len(variants)} active variants (excluded/ skipped)")
    prompts = [_build_variant_prompt(v, pattern_lookup, strategy, hw_target)
               for v in variants]
    print(f"Built {len(prompts)} prompts (strategy={strategy}, hw={hw_target})")
    print(f"Submitting to {model} on {MODELS[model]['gpu']} "
          f"(max {max_concurrent} parallel containers)...")

    server = VLLMServer.with_options(
        gpu=MODELS[model]["gpu"],
        max_containers=max_concurrent,
    )(model_key=model)

    # Chunk into batches; each batch goes to one container, vLLM batches
    # within the container via continuous batching.
    batch_size = max(1, len(prompts) // max(1, max_concurrent))
    batches = [prompts[i:i+batch_size]
               for i in range(0, len(prompts), batch_size)]
    batch_variants = [variants[i:i+batch_size]
                       for i in range(0, len(variants), batch_size)]
    print(f"Splitting into {len(batches)} batches of ~{batch_size} prompts each")

    # Open the output CSV up-front and stream results in as each batch
    # completes — that way a mid-sweep failure preserves the completed
    # work instead of losing everything.
    out_path = Path(output)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    err_path = out_path.with_suffix(".errors.csv")
    fail_path = out_path.with_suffix(".failed_variants.txt")

    n_ok, n_err, n_variants_done = 0, 0, 0
    failed_variant_ids: list[str] = []

    with open(out_path, "w", newline="") as fout, \
         open(err_path, "w", newline="") as ferr:
        ok_w = csv.writer(fout)
        ok_w.writerow(["variant_id", "pattern_id", "category", "model",
                       "strategy", "hw_target", "raw_output_chars",
                       "raw_output", "raw_reasoning_chars",
                       "raw_reasoning"])
        err_w = csv.writer(ferr)
        err_w.writerow(["batch_idx", "variant_id_first", "n_variants",
                        "exception_type", "exception_message"])

        # return_exceptions=True surfaces per-batch failures in-band, so
        # one dead container doesn't kill the whole sweep.
        batch_results = server.generate_batch.map(
            batches, order_outputs=True, return_exceptions=True,
        )

        for batch_idx, (batch_out, batch_vs) in enumerate(
                zip(batch_results, batch_variants)):
            if isinstance(batch_out, Exception):
                n_err += 1
                first_vid = batch_vs[0].variant_id if batch_vs else "?"
                err_w.writerow([batch_idx, first_vid, len(batch_vs),
                                type(batch_out).__name__, str(batch_out)])
                failed_variant_ids.extend(v.variant_id for v in batch_vs)
                print(f"  [batch {batch_idx+1}/{len(batches)}] "
                      f"FAILED ({type(batch_out).__name__}): "
                      f"{str(batch_out)[:120]}", flush=True)
                continue
            for v, r in zip(batch_vs, batch_out):
                # r is now a dict {"text": ..., "reasoning": ...}
                # Tolerate older string-returning workers.
                if isinstance(r, str):
                    text, reasoning = r, None
                else:
                    text     = r.get("text", "")
                    reasoning = r.get("reasoning")
                ok_w.writerow([
                    v.variant_id, v.pattern_id, v.category, model,
                    strategy, hw_target,
                    len(text), text,
                    len(reasoning) if reasoning else 0, reasoning or "",
                ])
                n_ok += 1
            n_variants_done += len(batch_vs)
            fout.flush(); ferr.flush()
            print(f"  [batch {batch_idx+1}/{len(batches)}] "
                  f"OK ({len(batch_vs)} variants, "
                  f"{n_variants_done}/{len(variants)} total)", flush=True)

    if failed_variant_ids:
        fail_path.write_text("\n".join(failed_variant_ids) + "\n")
        print(f"\n{n_err}/{len(batches)} batches failed "
              f"({len(failed_variant_ids)} variants).")
        print(f"  Failed variant IDs: {fail_path}")
        print(f"  Per-batch error CSV: {err_path}")
        print(f"  Retry just the failed variants by passing them as --patterns "
              f"to scripts/evaluate.py, or rerun this script (it will skip "
              f"variants already in the output CSV if you also implement a "
              f"--skip-existing flag).")
    else:
        # No failures — drop the empty errors file.
        if err_path.exists() and err_path.stat().st_size <= 200:
            err_path.unlink()

    print(f"\nWrote {n_ok}/{len(variants)} successful completions to {out_path}")
    print(f"Next steps:")
    print(f"  1. Score: python3 scripts/score_completions.py {out_path} "
          f"--output {out_path.with_name(out_path.stem + '_scored.csv')}")
    print(f"  2. Faithfulness 2x2: python3 faithfulness/report_2x2.py "
          f"{out_path.with_name(out_path.stem + '_scored.csv')}")
