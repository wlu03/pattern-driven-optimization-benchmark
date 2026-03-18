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

| Parameter | Value |
|---|---|
| Base model | `Qwen/Qwen2.5-Coder-7B-Instruct` |
| Quantization | 4-bit (QLoRA) |
| LoRA rank | 16 |
| Max sequence length | 2048 |
| Epochs | 3 |
| Learning rate | 2e-4 |
| LR schedule | cosine |
| Batch size | 2 × 8 grad accum = 16 effective |

Requires a GPU with ~16GB VRAM (e.g. A100 40GB comfortably, RTX 3090 at the limit).

## Evaluating the Fine-Tuned Model

After serving the adapter or registering with Ollama, add the model to `../models.yaml` and run:

```bash
python3 ../evaluate_llm.py --model qwen2.5-coder-finetuned --strategy generic
python3 ../evaluate_llm.py --model qwen2.5-coder-finetuned --strategy taxonomy-guided
```
