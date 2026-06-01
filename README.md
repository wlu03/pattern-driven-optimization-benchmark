# Pattern-Driven LLM Code Optimization Benchmark

A benchmark for evaluating whether LLMs can optimize C code patterns that compilers **cannot** fix automatically. Each pattern is specifically selected because `-O3` leaves it unoptimized — the inefficiency is semantic, algorithmic, or data-structural, not syntactic.

Includes 27 base patterns across 7 categories, a variant generator producing 1,140 dataset entries (including 700 composed multi-pattern variants in `dataset/COMP/` spanning 23 distinct two- and three-pattern combinations), a 36-pattern post-cutoff held-out test set for contamination defense (`dataset/held_out/`), and an LLM evaluation pipeline with correctness checking, retry-on-failure, and performance measurement.

---

## What This Benchmark Measures

Most existing code benchmarks ask whether an LLM can *write* correct code. This benchmark asks a harder question: **can an LLM recognize and fix a specific class of performance inefficiency that a production compiler cannot?**

The patterns are organized by *why* the compiler fails to fix them:

| Category | Why the compiler can't fix it | Example |
|---|---|---|
| Semantic Redundancy | Cross-TU side effects block hoisting | Calling `expensive_lookup()` every loop iteration |
| Input-Sensitive | Runtime distribution unknown at compile time | Using `qsort` on already-sorted data |
| Control-Flow | Branch condition depends on external function | Loop-invariant branch over a non-pure function |
| Data Structure | Layout change requires restructuring call sites | Array-of-Structs vs Struct-of-Arrays |
| Algorithmic | Asymptotic complexity change | O(2^n) Fibonacci recursion |
| Memory/IO | Access pattern semantics not visible to optimizer | Column-major traversal of row-major array |
| Human-Style | Code structure obscures optimization | Redundant temporaries, copy-paste loops |

---

## Key Findings (Qwen2.5-Coder-7B)

### Correctness by Prompting Strategy

| Strategy | Score | Note |
|---|---|---|
| `taxonomy-guided` | **16/16 (100%)** | Provide the full taxonomy; model self-diagnoses |
| `generic` | 15/16 (93.8%) | Plain "optimize this" prompt |
| `pattern-aware` | 15/16 (93.8%) | Tell the model which category the bug is in |

**Counterintuitive finding:** telling the model the specific pattern category (*pattern-aware*) is no better than — and sometimes worse than — not telling it anything. In one case (SR-2), the category hint caused the model to over-apply memoization and produce *slower* code. Providing the full taxonomy and letting the model self-diagnose consistently outperforms both.

### Performance Results (taxonomy-guided, compiled -O2)

| Pattern | Speedup vs Slow | Speedup vs Hand-Optimized | What the LLM did |
|---|---|---|---|
| SR-3 | **3743x** | 0.63x | Hoisted `strlen()` out of loop |
| SR-4 | **1212x** | 0.69x | Hoisted `expensive_lookup()` before loop |
| MI-4 | **9.2x** | 1.48x | Swapped column/row loop order |
| SR-2 | **2.3x** | 1.29x | Factored loop-invariant `alpha*beta` out |
| CF-3 | **1.7x** | 0.98x | Hoisted scalar multiply |
| SR-1, SR-5 | 1.2–1.3x | ~1.0x | Modest restructuring |
| CF-4 | ~1.0x | ~1.0x | Correct but no measurable speedup |
| IS-4 | **1.0x** | 0.10x | Correct but misses the 10x opportunity |
| DS-4 | ~1.0x | ~1.0x | Correct AoS loop; never restructures to SoA |
| IS-1, IS-3 | **0.6–0.8x** | — | Slower than the naive version |

### Where LLMs Excel

**Semantic Redundancy** — The model reliably recognizes and hoists loop-invariant work. SR-3 and SR-4 show 1000x+ speedups because the slow code repeats expensive computation on every iteration. This is the most text-book-like optimization: look for an expression in a loop that doesn't change, move it out. LLMs have clearly internalized this pattern deeply.

**Algorithmic rewrites** — AL-1 (O(2^n) Fibonacci → O(n) iterative) is handled correctly and consistently. The model knows the canonical DP rewrite.

**Cache-friendly access** — MI-4 (column vs row major) is fixed correctly by swapping loop order. Once the model has the taxonomy hint, it finds this immediately.

### Where LLMs Struggle

**Input-Sensitive patterns** — The hardest category. IS-4 requires sampling the input at runtime, detecting whether it is already sorted or reverse-sorted, and branching to a specialized algorithm. The model almost always just calls `qsort()` — correct, safe, but misses the 10x speedup the reference captures. This class of optimization requires reasoning about *data distributions at runtime*, which LLMs do not model well.

**Data structure layout** — DS-4 measures AoS vs SoA. The model correctly loops over `p[i].mass` and passes correctness — but the actual optimization is restructuring `Particle[]` into a separate `double mass[]` array, which requires changing the call site's data model. The model never does this. It optimizes *within* the given data structure, not *across* it.

**Overhead addition** — IS-1 (sparse vector) and IS-3 (adaptive sort) are made *slower* by the model in the generic and taxonomy strategies. In IS-1, the model adds a redundant inner loop reorganization that increases work. This shows the model sometimes mistakes "more code" for "more optimized."

### The Prompt Strategy Effect in Detail

Three patterns show large performance divergence across strategies:

**SR-2** (spread: 8x across strategies)
- Generic: 0.29x — model expanded `alpha*beta` *into* the loop, adding work
- Pattern-aware: 1.14x — correct separation of sums
- Taxonomy: 2.31x — fully factors out both loop-invariant terms

**IS-4** (spread: 12.8x across strategies)
- Generic / Taxonomy: 1.0–1.3x — just calls `qsort()`
- Pattern-aware: **12.8x** — adds a sorted-check pre-scan, skips sort entirely if already ordered. The "Input-Sensitive" label pushed the model toward data-distribution thinking.

**MI-4** (spread: 8.8x across strategies)
- Generic: 1.1x — kept column-major order (the slow version)
- Pattern-aware / Taxonomy: 8–9x — swapped to row-major

**Implication:** for complex patterns, prompt strategy matters as much as model capability. The taxonomy-guided approach wins on *correctness*, but pattern-aware wins on *IS-4 performance* — suggesting that different prompt strategies activate different optimization instincts. A hybrid approach (taxonomy for diagnosis, category label for input-sensitive patterns) may be optimal.

---

## Novel Aspects

### 1. Compiler-Resistance as the Selection Criterion
All patterns are selected specifically because `-O3` *cannot* fix them. This is a harder and more practically useful bar than "can the LLM write this from scratch." The benchmark measures a capability gap that is real in production systems: compilers are excellent at micro-optimization but blind to semantic-level inefficiency.

### 2. Dual Performance Baseline
Results are reported as both `speedup vs slow` and `speedup vs hand-optimized reference`. This separates two failure modes:
- Code that is correct but doesn't improve (speedup vs slow ≈ 1.0x, seen in DS-4, IS-4)
- Code that is correct, faster than slow, but still far from optimal (seen in SR-3, SR-4 where LLM is 3000x better than slow but 0.63x vs reference)

### 3. Taxonomy-Guided Self-Diagnosis
Providing a structured inefficiency taxonomy and asking the model to first diagnose then fix outperforms both bare prompting and targeted hints. This suggests a general prompting principle: structured checklists for open-ended analysis tasks outperform direct instruction.

### 4. Retry Loop with Compiler Feedback
The evaluation pipeline feeds compile errors and wrong-output signals back to the model as structured feedback ("your code failed with error: ..."). This substantially improves pass rates and is a practical pattern for autonomous code generation systems.

### 5. The Pattern-Aware Backfire Effect
Giving the model a category label sometimes *hurts* performance vs giving no label. This happens when the label activates a pattern the model over-applies. It is a concrete example of how context can mislead rather than help a model — relevant to RAG and prompt injection research.

### 6. Two-Axis Faithfulness Verdict

Runtime correctness and observed speedup do not distinguish three substantively different outcomes:
**(i)** the model applied the *expected* structural transformation,
**(ii)** the model applied a *different valid* transformation that produces the same answer faster (e.g., we expected hoisting, the model vectorized), or
**(iii)** the model produced code that happens to be correct on the single configuration tested but does not generalize (hardcoded constant, special-case for the random seed, etc.).

The faithfulness layer (`faithfulness/`) is designed to separate these. Each model output is scored along two independent axes and routed into one of four cells:

|                       | **Expected shape**     | **Alternative**            |
|-----------------------|------------------------|----------------------------|
| **Equivalent**        | `FAITHFUL`             | `FAITHFUL_ALTERNATIVE`     |
| **Not equivalent**    | `STRUCTURAL_ONLY`      | `FAILED`                   |

- **Equivalent** is determined empirically by `differential_equivalence` (in `faithfulness/equivalence.py`): the candidate must pass correctness across nine input configurations (3 problem sizes × 3 seeds + 4 adversarial distributions) that exercise the `BENCH_N`/`BENCH_SEED`/`BENCH_DIST` hooks in every harness. A model that hardcodes the answer for the default config fails this check.
- **Expected shape** is determined by the AST-based per-pattern checkers in `faithfulness/checkers/` (e.g., for loop-invariant hoisting: "the expensive call no longer appears inside any loop body"). When pycparser fails to parse the model output, the checker falls through to regex matching, and the fallback rate is reported per pattern by `faithfulness/report_2x2.py` as a first-class data-quality signal.

**Evidence and design rationale.**

The two-axis schema follows the empirical finding from *Wu et al. (FSE 2025, [arXiv:2504.04321](https://arxiv.org/abs/2504.04321))* on optimization-guided equivalence transformation: specify the expected transformation up-front via AST conditions, then verify equivalence empirically via differential execution. The cascade architecture (semantic-first, structural-second) follows *Le-Cong et al., **INVALIDATOR**, IEEE TSE 2023 ([arXiv:2301.01113](https://arxiv.org/abs/2301.01113))*, which targets the closely analogous problem of distinguishing genuinely correct automated-program-repair patches from overfitting ones and reports that the hybrid cascade beats either tier alone by 11–26 percentage points on 885 Defects4J patches.

**Why the verdict does *not* condition on the model's reasoning trace.**

A natural extension would be to read the model's stated optimization plan (Claude extended thinking, o-series reasoning summaries, DeepSeek-R1 chains) and score whether the plan matches the emitted code. We deliberately don't, on three converging pieces of evidence:

- *Chen, Benton et al. (Anthropic, [arXiv:2505.05410](https://arxiv.org/abs/2505.05410), May 2025)* report that frontier reasoning models verbalize the cues actually driving their answers only **25–39%** of the time on average — and in reward-hacking environments, they exploit hints **>99%** of the time while verbalizing them **<2%**, "constructing fake rationales for why the incorrect answer was in fact right."
- *Lanham et al. ([arXiv:2307.13702](https://arxiv.org/abs/2307.13702), 2023)* show, via causal interventions (Early Answering, Adding Mistakes, Paraphrasing), that the CoT is load-bearing for the final answer only sometimes — Answering-Over-Chain values range from 44% on AQuA to 2% on ARC Easy on the same model.
- *Turpin et al. (NeurIPS 2023, [arXiv:2305.04388](https://proceedings.neurips.cc/paper_files/paper/2023/hash/ed3fea9033a80fea1376299fa7863f4a-Abstract-Conference.html))* document up to **36% accuracy swings** on BIG-Bench Hard from biasing features (e.g., reordering MCQ options) that CoT never acknowledged.

A faithfulness scorer that reads the model's stated plan would inherit all of these unreliabilities. The benchmark judges the **artifact** (the diff, the AST, the runtime behavior across the differential sweep), not the **narrative**.

**Known limitation.** The cascade does not currently include an LLM-as-judge tier for the `FAITHFUL_ALTERNATIVE` cell, which means the benchmark detects that the model achieved equivalence via an alternative transformation but doesn't auto-label which alternative. Adding one is straightforward (judge the diff, not the CoT — see above) and would directly address an open question: no published head-to-head comparison currently exists between structural checkers and LLM judges on code-optimization faithfulness specifically.

---

## Getting Started

```bash
pip install -r requirements.txt   # anthropic openai google-generativeai pyyaml

# Generate dataset variants
python3 scripts/generate.py --patterns all --variants 30 --output dataset/
python3 scripts/batch_test.py dataset/   # verify generated dataset compiles + is correct
```

### API Keys

```bash
export ANTHROPIC_API_KEY=sk-ant-...   # Claude
export OPENAI_API_KEY=sk-...          # GPT / o3
export DEEPSEEK_API_KEY=sk-...        # DeepSeek
export GOOGLE_API_KEY=...             # Gemini
export TOGETHER_API_KEY=...           # Llama / Mistral / Qwen / Gemma / Phi / Falcon
export GROQ_API_KEY=...               # same models, faster inference
# Ollama (local, no key): ollama serve && ollama pull qwen2.5-coder:7b
```

### Local Inference with Ollama

```bash
brew services start ollama            # macOS background daemon
ollama pull qwen2.5-coder:7b          # ~5GB GGUF download
python3 scripts/evaluate.py --model qwen2.5-coder-7b-ollama --strategy taxonomy-guided
```

### Run Evaluations

```bash
# See all available models
python3 scripts/evaluate.py --list-models

# Dry run — preview prompts without calling API
python3 scripts/evaluate.py --dry-run --model gpt-4o --strategy taxonomy-guided

# Single model, single strategy
python3 scripts/evaluate.py --model claude-sonnet-4-6  --strategy taxonomy-guided --output results.csv
python3 scripts/evaluate.py --model gpt-4o             --strategy pattern-aware   --output results.csv
python3 scripts/evaluate.py --model qwen2.5-coder-7b-ollama --strategy generic    --output results.csv

# All models at once
python3 scripts/evaluate.py --all-models --strategy taxonomy-guided --output results.csv

# Specific patterns only
python3 scripts/evaluate.py --model gpt-4o --patterns SR-3,IS-4,MI-4 --strategy pattern-aware
```

### Prompting Strategies

| Strategy | Flag | What it does |
|---|---|---|
| Generic | `--strategy generic` | "Optimize this C code" — no hints |
| Pattern-aware | `--strategy pattern-aware` | Tells the model the category and pattern name |
| Taxonomy-guided | `--strategy taxonomy-guided` | Full 7-category taxonomy; model diagnoses then fixes |
| Diagnosis-only | `--strategy diagnosis` | Asks for analysis only, no optimization |
| Hardware-target | `--strategy hardware-target --target arm_apple` | Targets specific hardware |

Hardware targets: `generic`, `x86_avx2`, `arm_neon`, `arm_apple`, `arm_cortex`, `x86_64`, `gpu_cuda`, `cpu`

### Supported Models

| Family | Example IDs | Key |
|---|---|---|
| Claude (Anthropic) | `claude-sonnet-4-6`, `claude-opus-4-6`, `claude-haiku-4-5` | `ANTHROPIC_API_KEY` |
| GPT / o3 (OpenAI) | `gpt-4o`, `gpt-4o-mini`, `o3-mini` | `OPENAI_API_KEY` |
| DeepSeek | `deepseek-v3`, `deepseek-r1` | `DEEPSEEK_API_KEY` |
| Gemini (Google) | `gemini-2-flash`, `gemini-2-pro` | `GOOGLE_API_KEY` |
| Llama 3.x (Meta) | `llama-3.1-70b-together`, `llama-3.1-8b-groq` | `TOGETHER_API_KEY` / `GROQ_API_KEY` |
| Mistral / Mixtral | `mistral-7b-together`, `mixtral-8x7b-groq` | `TOGETHER_API_KEY` / `GROQ_API_KEY` |
| Gemma 2 (Google) | `gemma2-9b-together` | `TOGETHER_API_KEY` |
| Phi-3/4 (Microsoft) | `phi-3-mini-together`, `phi-3-medium-together` | `TOGETHER_API_KEY` |
| Qwen 2.5 (Alibaba) | `qwen2.5-7b-together`, `qwen2.5-72b-together`, `qwen2.5-coder-7b-ollama` | `TOGETHER_API_KEY` / Ollama |
| Falcon | `falcon-7b-together`, `falcon-40b-together` | `TOGETHER_API_KEY` |

To add a new model, append an entry to `models.yaml` — no code changes required.

---

## Project Structure

```
.
├── README.md
├── LICENSE
├── requirements.txt
├── models.yaml                       # Model registry (add new models here)
│
├── pdob_core/                        # Core library — import as `pdob_core.*`
│   ├── __init__.py                   # Re-exports: PATTERNS, compile_and_run, evaluate_pattern, ...
│   ├── compiler.py                   # compile_and_run, normalize/sanitize helpers
│   ├── evaluator.py                  # EvalResult dataclass + evaluate_pattern / evaluate_variant
│   ├── dataset_evaluator.py          # Multi-TU compile path for dataset/ variants
│   ├── prompts.py                    # Prompt builders + HW_TARGET_DESCRIPTIONS
│   ├── models.py                     # load_model_config + provider call functions
│   ├── patterns/                     # PatternEntry + all 27 PATTERNS (one file per category)
│   └── generators/                   # Variant generator (one file per category) + dataset glue
│
├── scripts/                          # CLI entry points
│   ├── evaluate.py                   # LLM evaluation driver — was `evaluate_llm.py`
│   ├── generate.py                   # Dataset generator    — was `generate_variants.py`
│   ├── test_variant.py               # Test one generated variant (multi-TU + helper.c)
│   ├── batch_test.py                 # Test all generated variants
│   ├── measure_compiler_fixable.py   # Per-variant compiler-fix measurement (5 regimes)
│   └── run_multi_input.py            # Run a pattern across multiple n × seed × distribution configs
│
├── notebooks/
│   ├── ablation_study.ipynb          # Ablation analysis notebook (local)
│   └── ablation_study_colab.ipynb    # Ablation analysis notebook (Colab)
│
├── docs/
│   ├── implementation.tex            # Paper section: pipeline + harness
│   └── related_work.tex              # Paper section: related work
│
├── faithfulness/
│   ├── checkers/                     # AST-based per-pattern structural checkers (one file per category)
│   │   └── _base.py                  # Verdict + FaithfulnessResult + TwoAxisVerdict / Cell schema
│   ├── equivalence.py                # Tier 1: differential_equivalence + two_axis_verdict
│   ├── evaluate_faithfulness.py      # Driver for faithfulness scoring
│   └── report_2x2.py                 # Faithful×fast 2×2 matrix + pycparser parse-success rate
│
├── fine_tune/                        # QLoRA fine-tuning workflow (independent)
│   ├── README.md
│   ├── prepare_finetune_data.py
│   ├── finetune_lora.py
│   ├── merge_and_export.py
│   ├── lora_finetune_tutorial.ipynb
│   ├── train.jsonl / val.jsonl       # Prepared training data
│   └── lora_fine_tuning/             # Trained adapter checkpoints
│
└── dataset/                          # Generated variants (1,140 main + 36 held-out)
    ├── index.json / index.csv
    ├── <PID>/<PID>_v<NNN>/           # 27 base patterns × ~15 variants + COMP × 700
    │   ├── slow.c                    # Inefficient code
    │   ├── fast.c                    # Hand-optimized reference
    │   ├── helper.c                  # `expensive_*` noinline functions (where applicable)
    │   ├── test.c                    # Compile + verify harness
    │   └── metadata.json             # Pattern ID, difficulty, description
    └── held_out/                     # 36 post-2026-05 contamination-defense patterns
        ├── README.md                 # Per-wave provenance + per-pattern citations
        ├── HO_{AL,CF,DS,HR,IS,MI,SR}/ # Categorized like the main set, never trained on
        └── ...
```

---

## Fine-Tuning

The dataset can be used to LoRA fine-tune a base model and measure whether fine-tuning improves optimization capability.

```bash
# Generate JSONL training data from dataset/
cd fine_tune
python3 prepare_finetune_data.py \
  --strategies generic pattern-aware taxonomy-guided \
  --split 0.9 \
  --train train.jsonl \
  --val val.jsonl

# See fine_tune/lora_finetune_tutorial.ipynb for step-by-step training with Unsloth + TRL
```

The notebook covers: LoRA adapter setup, QLoRA 4-bit quantization, SFTTrainer configuration, loss curve analysis, inference testing, and serving the fine-tuned adapter via Ollama.
