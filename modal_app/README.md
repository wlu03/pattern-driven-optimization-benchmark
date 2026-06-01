# Modal Compute Setup

Modal (https://modal.com) hosts the LLM evaluation and LoRA fine-tune passes
for this benchmark. Modal's `.map()` primitive fans out the 1,244-variant
inference sweep across 10–50 GPU containers, and its official Unsloth
recipe handles the 7B QLoRA fine-tune end-to-end on a single L40S.

## One-time setup

```bash
pip install modal
modal token new                # browser auth — Modal saves the token under ~/.modal
modal volume create pdob-hf-cache
modal volume create pdob-vllm-cache
modal volume create pdob-adapters
modal volume create pdob-dataset
```

Apply for free credits at https://modal.com/signup ($30/mo on Starter; up to
$10k academic grants for research projects).

## Inference: evaluate one model on the full dataset

```bash
modal run modal_app/inference.py::evaluate_all \
    --model qwen2.5-coder-7b \
    --strategy taxonomy-guided \
    --output results/qwen25_coder_7b_taxonomy.csv
```

Estimated time / cost (verified per [modal.com/pricing](https://modal.com/pricing)):

| Model        | GPU       | $/hr  | Wall-clock @ 10 containers | Cost |
|--------------|-----------|-------|----------------------------|------|
| 1.5B         | T4        | $0.59 | ~3 min                     | ~$0.30 |
| 7B           | A10G      | $1.10 | ~6 min                     | ~$1.10 |
| 14B          | L40S      | $1.95 | ~10 min                    | ~$3.25 |
| 32B          | A100-80GB | $2.50 | ~15 min                    | ~$6.25 |
| 70B          | H100      | $3.95 | ~25 min                    | ~$6.60 |

Includes vLLM warm-up. First-ever run on a model pulls weights from HF (~30s
for 7B, ~2 min for 70B); the `pdob-hf-cache` Volume caches them for subsequent
runs.

## Fine-tune: QLoRA on Modal L40S

First prepare training data locally (excludes held-out by default):

```bash
cd fine_tune
python3 prepare_finetune_data.py --strategies taxonomy-guided \
    --split 0.9 --train train.jsonl --val val.jsonl
```

Then submit to Modal:

```bash
modal run modal_app/finetune.py::main \
    --base-model Qwen/Qwen2.5-Coder-7B-Instruct \
    --train-jsonl fine_tune/train.jsonl \
    --val-jsonl   fine_tune/val.jsonl \
    --output-name qwen25-coder-7b-taxonomy
```

Estimated: 1.5–3 h on L40S ($1.95/hr) for a 3-epoch 7B QLoRA on ~2,000
examples → **$3–9** total. Pull the adapter:

```bash
modal volume get pdob-adapters qwen25-coder-7b-taxonomy/ \
    ./fine_tune/lora_fine_tuning/qwen25-coder-7b-taxonomy/
```

## Pareto-frontier model shortlist

Wired in `modal_app/inference.py::MODELS` (see file for the full dict).
The shortlist spans the quality vs cost frontier for the open-source
optimization-capability axis (closed APIs Claude/GPT/Gemini run via
`scripts/evaluate.py` on the laptop, not via Modal):

| Model | Size | GPU | LiveCodeBench | Why |
|---|---|---|---|---|
| Qwen2.5-Coder-1.5B | 1.5B | T4 | ~16 | ultra-light anchor |
| DeepSeek-R1-Distill-Qwen-1.5B | 1.5B | T4 | ~16 | reasoning at 1.5B |
| Qwen2.5-Coder-7B | 7B | A10G | ~37 | best 7B coder |
| DeepSeek-R1-Distill-Qwen-7B | 7B | A10G | ~37 | reasoning at 7B |
| Qwen2.5-Coder-14B | 14B | L40S | ~50 | price/perf knee |
| Codestral-22B | 22B | L40S | ~38 | Mistral-lineage sanity check |
| Qwen2.5-Coder-32B | 32B | A100-80GB | 70.7 | best open ≤70B |
| DeepSeek-R1-Distill-Qwen-32B | 32B | A100-80GB | 57.2 | reasoning twin |
| Llama-3.3-70B-Instruct | 70B | H100 | ~35 | general-capable contrast |

Adding a model: append an entry to the `MODELS` dict in `inference.py`.

## Cost calculator

Total budget to run the full Pareto-frontier ablation (each model × each of
4 prompting strategies = ~36 sweeps over 1,244 variants):

| Model | Cost/sweep | 4 sweeps |
|---|---|---|
| 1.5B (×2) | $0.30 | $1.20 each → $2.40 |
| 7B   (×2) | $1.10 | $4.40 each → $8.80 |
| 14B       | $3.25 | $13 |
| 22B       | $3.25 | $13 |
| 32B (×2)  | $6.25 | $25 each → $50 |
| 70B       | $6.60 | $26.40 |
| **Total** |       | **~$113** |

Plus fine-tunes (3 strategies × 1 base 7B): $9–27. Grand total ~$140 for the
full ablation. Modal's $30 free Starter credit covers ~25% of that.

## Alternatives evaluated

- **RunPod Serverless** (H100 PCIe $1.99/hr, A100 80GB $1.19/hr): ~40-50%
  cheaper than Modal but no `.map()` primitive. Worth it if you've already
  containerized your stack.
- **Together.ai fine-tune API** ($0.48/M tokens for LoRA ≤16B): for our
  ~12M-token QLoRA workload, ~$6 — competitive with Modal but you skip
  custom training loops.
- **Lambda Cloud** (H100 SXM $4.29/hr): no scale-to-zero, bad for sporadic
  eval. Better for long-running training.
