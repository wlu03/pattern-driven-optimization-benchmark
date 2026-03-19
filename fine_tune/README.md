# Fine-Tuning

LoRA fine-tune a code model on the benchmark dataset so it learns to recognize and fix the compiler-resistant inefficiency patterns.

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
  --strategies generic pattern-aware \
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
| LoRA rank | 16 | Increase to 64 if underfitting |
| LoRA alpha | 32 (2× rank) | Scales adapter update magnitude |
| LoRA target modules | all attention + MLP projections | q/k/v/o + gate/up/down |
| Max sequence length | 2048 | Increase to 4096 for longer examples |
| Epochs | 10 (with early stopping) | Stops after 3 epochs without eval loss improvement |
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
