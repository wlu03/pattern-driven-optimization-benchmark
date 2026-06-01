# Fine-Tuning

LoRA fine-tune a code model on the benchmark dataset so it learns to recognize and fix the compiler-resistant inefficiency patterns, then evaluate the fine-tuned model's **transfer** to the held-out test set (post-cutoff patterns the model has never seen during training).

## Train / val / held-out split

The benchmark explicitly partitions data into three non-overlapping sets:

| Set | Location | Count | Used for |
|---|---|---|---|
| **Train** | `dataset/<CAT>_<N>/<PID>_v<NNN>/` + `dataset/COMP/` | ~440 base + ~700 COMP variants | Fine-tuning corpus (after 90/10 split into train/val) |
| **Val** | sampled from Train via `--split 0.9` | ~10% of above | Loss monitoring during training |
| **Held-out** | `dataset/held_out/HO_<CAT>/HO-<CAT>-<N>_v000/` | 29 patterns | Final evaluation only — NEVER in training |

**Contamination defense (CRITICAL).** `prepare_finetune_data.py` excludes `dataset/held_out/` by default. The `--exclude held_out` flag is on by default; you'll see `[skip] held_out/` in stderr when training data is built. The held-out set post-dates the announced training cutoffs of all evaluated frontier models (creation_date 2026-05-29 onward), following the LiveBench (arXiv:2406.19314) and SWE-bench-Live (arXiv:2505.23419) temporal-boundary precedent — see `docs/implementation.tex` §Held-Out Contamination Defense for the full methodology.

To intentionally include held-out in training (for a contamination-control experiment ONLY), pass `--include-held-out`. The script emits a loud `WARNING` to stderr making clear that any contamination-defense claim is invalid for that run.

## The transfer experiment

The core experimental question this workflow supports: **does fine-tuning on the 590 base+COMP variants transfer to held-out patterns?**

```bash
# Step 1 — build training data (held_out automatically excluded)
python3 fine_tune/prepare_finetune_data.py \
    --dataset ../dataset --strategies generic pattern-aware taxonomy-guided \
    --split 0.9 --train fine_tune/train.jsonl --val fine_tune/val.jsonl

# Step 2 — fine-tune (your usual workflow)
python3 fine_tune/finetune_lora.py --train fine_tune/train.jsonl --val fine_tune/val.jsonl

# Step 3 — evaluate BASE model on held-out
python3 scripts/evaluate.py --model qwen2.5-coder-7b-ollama \
    --strategy taxonomy-guided --faithfulness \
    --dataset dataset/held_out --output results_base_holdout.csv

# Step 4 — evaluate FINE-TUNED model on the SAME held-out patterns
python3 scripts/evaluate.py --model qwen2.5-coder-7b-finetuned \
    --strategy taxonomy-guided --faithfulness \
    --dataset dataset/held_out --output results_ft_holdout.csv

# Step 5 — paired transfer analysis (per-category delta + Wilcoxon p)
python3 scripts/finetune_transfer_eval.py \
    --base-csv results_base_holdout.csv \
    --finetuned-csv results_ft_holdout.csv \
    --metric faithful \
    --out transfer_eval/

# Step 6 (optional) — cross-pattern transfer matrix restricted to held-out
python3 scripts/transfer_analysis.py results_ft_holdout.csv \
    --held-out-only --out figs/transfer_holdout.pdf
```

The headline result is the Wilcoxon p-value plus the per-category delta table: does the fine-tuned model do significantly better on held-out, and which categories benefit most? If fine-tuning improves SR but hurts AL, that's a per-category finding — not a single aggregate number.

## Files

| File | Purpose |
|---|---|
| `prepare_finetune_data.py` | Convert `dataset/` into a JSONL training file |
| `finetune_lora.py` | QLoRA fine-tune `Qwen2.5-Coder-7B-Instruct` with Unsloth + TRL |
| `merge_and_export.py` | Merge LoRA adapter into base weights and export to GGUF for Ollama |
| `lora_finetune_tutorial.ipynb` | Step-by-step notebook walkthrough |

## Quickstart

```bash
pip install unsloth datasets trl

# 1. Generate training data (960 variants × 2 strategies = 1920 examples)
python3 prepare_finetune_data.py \
  --strategies generic pattern-aware taxonomy-guided \
  --split 0.9 \
  --train train.jsonl \
  --val val.jsonl

# 2. Fine-tune
python3 finetune_lora.py --train train.jsonl --val val.jsonl

# 3a. Serve with vLLM (no merge needed)
vllm serve Qwen/Qwen2.5-Coder-7B-Instruct \
  --enable-lora \
  --lora-modules finetuned=lora_adapter/

# 3b. Or merge + export to GGUF for Ollama
python3 merge_and_export.py
ollama create qwen2.5-coder-finetuned -f Modelfile
```

## Data Preparation

`prepare_finetune_data.py` walks `../dataset/` and builds chat-format examples:

- **User**: prompt asking to optimize `slow.c`
- **Assistant**: `fast.c` with the function renamed to `optimized`

Three prompt strategies are available:

| Strategy | Flag | Description |
|---|---|---|
| Generic | `generic` | "Optimize this C code" — no hints |
| Pattern-aware | `pattern-aware` | Tells the model the category and pattern name |
| Taxonomy-guided | `taxonomy-guided` | Provides the full 7-category inefficiency taxonomy |

```bash
# Preview dataset statistics without writing files
python3 prepare_finetune_data.py --stats

# All three strategies (2880 examples)
python3 prepare_finetune_data.py --strategies generic pattern-aware taxonomy-guided
```

## Training Details

`finetune_lora.py` defaults:

| Parameter | Value | Notes |
|---|---|---|
| Base model | `Qwen/Qwen2.5-Coder-7B-Instruct` | Instruct variant for chat template alignment |
| Quantization | 4-bit NF4 (QLoRA) | ~4× less VRAM vs. full BF16 |
| LoRA rank | 8 | Increase to 16-64 if underfitting |
| LoRA alpha | 16 (2× rank) | Scales adapter update magnitude |
| LoRA target modules | all attention + MLP projections | q/k/v/o + gate/up/down |
| Max sequence length | 2048 | Increase to 4096 for longer examples |
| Epochs | 10 (with early stopping) | Stops after 2 epochs without eval loss improvement |
| Learning rate | 2e-4 | Cosine schedule with 5% warmup |
| Batch size | 2 × 8 grad accum = 16 effective | |
| Optimizer | `adamw_torch_fused` | Fastest AdamW for PyTorch 2.x |
| Gradient clipping | 0.3 | Guards against LoRA adapter divergence |
| Mixed precision | BF16 + TF32 | BF16 activations, TF32 tensor cores (A100) |
| Packing | enabled | Concatenates short examples — eliminates padding waste |
| Response-only loss | enabled | Loss masked to assistant outputs only |

Requires a GPU with ~16GB VRAM (e.g. A100 40GB comfortably, RTX 3090 at the limit).

## Best Practices (from research)

### Data quality over quantity
1,000 high-quality verified examples can match 50,000 mediocre ones (LIMA, 2023). For code, prefer execution-verified solutions with test cases over text-plausible ones. The synthetic data pipeline here uses real `slow.c`/`fast.c` pairs that are compiled and benchmarked, making them ideal training signal.

### Why response-only loss matters
By default, SFT computes loss over the entire sequence (system prompt + user message + assistant response). This wastes capacity on tokens the model will never generate at inference. Masking the loss to assistant outputs only produces measurably better instruction following.

### Overfitting signals to watch
- Training loss keeps dropping but eval loss plateaus or rises → stop early
- Model outputs become repetitive or template-locked → reduce epochs or add `lora_dropout=0.05`
- `max_grad_norm=0.3` fires frequently → learning rate too high, reduce by 2×

### Going further: DPO on top of SFT
After SFT, a DPO stage on ~2K preference pairs (correct optimization vs. near-miss) adds ~5% further improvement. Use `lr=5e-6` (10-100× lower than SFT) and `beta=0.1`.

### Evaluation beyond loss
Validation loss alone does not predict benchmark performance. After training, evaluate with:
- **EvalPlus** (HumanEval+ / MBPP+) — extended test cases, harder to saturate
- **LiveCodeBench** — contamination-free, rolling benchmark with post-cutoff problems
- **BigCodeBench** — multi-library software engineering tasks

Use `pass@1` (greedy) as the primary metric. Do not rely on HumanEval alone — top models now exceed 90% pass@1, making it nearly saturated.

## Evaluating the Fine-Tuned Model

After serving the adapter or registering with Ollama, add the model to `../models.yaml` and run:

```bash
python3 ../evaluate_llm.py --model qwen2.5-coder-finetuned --strategy generic
python3 ../evaluate_llm.py --model qwen2.5-coder-finetuned --strategy taxonomy-guided
```
