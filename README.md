# Pattern-Driven LLM Code Optimization Benchmark

A benchmark for evaluating whether LLMs can optimize C code patterns that compilers **cannot** fix automatically. Each pattern is specifically selected because `-O3` leaves it unoptimized — the inefficiency is semantic, algorithmic, or data-structural, not syntactic.

Includes 16 evaluated patterns across 7 categories, a variant generator to produce hundreds of dataset entries, and an LLM evaluation pipeline with correctness checking, retry-on-failure, and performance measurement.

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
| CF-1/2/4 | ~1.0x | ~1.0x | Equal — compiler already handles these |
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

---

## Getting Started

```bash
pip install -r requirements.txt   # anthropic openai google-generativeai pyyaml

# Generate dataset variants
python3 generate_variants.py --patterns all --variants 30 --output dataset/
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
python3 evaluate_llm.py --model qwen2.5-coder-7b-ollama --strategy taxonomy-guided
```

### Run Evaluations

```bash
# See all available models
python3 evaluate_llm.py --list-models

# Dry run — preview prompts without calling API
python3 evaluate_llm.py --dry-run --model gpt-4o --strategy taxonomy-guided

# Single model, single strategy
python3 evaluate_llm.py --model claude-sonnet-4-6  --strategy taxonomy-guided --output results.csv
python3 evaluate_llm.py --model gpt-4o             --strategy pattern-aware   --output results.csv
python3 evaluate_llm.py --model qwen2.5-coder-7b-ollama --strategy generic    --output results.csv

# All models at once
python3 evaluate_llm.py --all-models --strategy taxonomy-guided --output results.csv

# Specific patterns only
python3 evaluate_llm.py --model gpt-4o --patterns SR-3,IS-4,MI-4 --strategy pattern-aware
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
├── Makefile
│
├── main.c                             # Runs all patterns at O0 and O3 for reference
├── harness/
│   └── bench_harness.h               # Timing, verification, reporting utilities
├── patterns/
│   ├── cat1_semantic_redundancy.c    # SR-1 to SR-5  (5 patterns)
│   ├── cat2_input_sensitive.c        # IS-1 to IS-4  (4 patterns)
│   ├── cat3_control_flow.c           # CF-1 to CF-4  (4 patterns)
│   ├── cat4_human_style.c            # HR-1 to HR-5  (5 patterns)
│   ├── cat5_data_structure.c         # DS-1 to DS-4  (4 patterns)
│   ├── cat6_algorithmic.c            # AL-1 to AL-4  (4 patterns)
│   └── cat7_memory_io.c              # MI-1 to MI-4  (4 patterns)
│
├── evaluate_llm.py                   # LLM evaluation pipeline (correctness + performance)
├── generate_variants.py              # Generates N slow/fast C pairs per pattern
├── prepare_finetune_data.py          # Converts dataset to JSONL for LoRA fine-tuning
├── lora_finetune_tutorial.ipynb      # Step-by-step LoRA fine-tuning guide
├── models.yaml                       # Model registry (add new models here)
│
├── scripts/
│   ├── test_variant.py               # Test one generated variant
│   └── batch_test.py                 # Test all generated variants
│
└── dataset/                          # Generated variants
    ├── index.json
    ├── index.csv
    └── SR_1/SR-1_v000/
        ├── slow.c                    # Inefficient code
        ├── fast.c                    # Hand-optimized reference
        ├── test.c                    # Compile + verify harness
        └── metadata.json             # Pattern ID, difficulty, description
```

---

## Fine-Tuning

The dataset can be used to LoRA fine-tune a base model and measure whether fine-tuning improves optimization capability.

```bash
# Generate JSONL training data from dataset/
python3 prepare_finetune_data.py \
  --strategies generic pattern-aware taxonomy-guided \
  --split 0.9 \
  --train train.jsonl \
  --val val.jsonl

# See lora_finetune_tutorial.ipynb for step-by-step training with Unsloth + TRL
```

The notebook covers: LoRA adapter setup, QLoRA 4-bit quantization, SFTTrainer configuration, loss curve analysis, inference testing, and serving the fine-tuned adapter via Ollama.
