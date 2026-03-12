# Pattern-Driven LLM Code Optimization Benchmark
A benchmark framework for evaluating whether LLMs can optimize code patterns that compilers cannot. Contains 28 hand-written inefficiency patterns across 7 categories, a variant generator to produce hundreds of dataset entries, and an LLM evaluation pipeline to measure optimization quality.

# Starting
```bash
pip install -r requirements.txt   # anthropic openai google-generativeai pyyaml

make run                          # run all 28 base patterns

python3 generate_variants.py --patterns all --variants 30 --output dataset/
python3 scripts/batch_test.py dataset/   # verify generated dataset compiles + is correct
```

# LLM Evaluation

### Setup — set whichever API keys you have
```bash
export ANTHROPIC_API_KEY=sk-ant-...   # Claude
export OPENAI_API_KEY=sk-...          # GPT / o3
export DEEPSEEK_API_KEY=sk-...        # DeepSeek
export GOOGLE_API_KEY=...             # Gemini
export TOGETHER_API_KEY=...           # Llama / Mistral / Mixtral / Gemma / Phi / Qwen / Falcon
export GROQ_API_KEY=...               # same models, ultra-fast inference
# Ollama (local, no key): ollama serve && ollama pull llama3.1
```

### See all available models
```bash
python3 evaluate_llm.py --list-models
```

### Preview prompts without calling any API
```bash
python3 evaluate_llm.py --dry-run --model gpt-4o --strategy taxonomy-guided
```

### Run a single model
```bash
python3 evaluate_llm.py --model claude-sonnet-4-6  --strategy generic        --output results.csv
python3 evaluate_llm.py --model gpt-4o             --strategy pattern-aware  --output results.csv
python3 evaluate_llm.py --model deepseek-v3        --strategy taxonomy-guided --output results.csv
python3 evaluate_llm.py --model llama-3.1-70b-together --strategy generic    --output results.csv
python3 evaluate_llm.py --model llama3.1-ollama    --strategy generic        --output results.csv
```

### Run all models at once
```bash
python3 evaluate_llm.py --all-models --strategy generic --output results.csv
```

### Filter to specific patterns
```bash
python3 evaluate_llm.py --model gpt-4o --patterns SR-1,CF-2,AL-1 --strategy pattern-aware
```

### Prompting strategies

| Strategy | Flag | What it does |
|---|---|---|
| Generic | `--strategy generic` | "Optimize this C code" — no hints |
| Pattern-aware | `--strategy pattern-aware` | Tells the LLM the category and pattern name |
| Taxonomy-guided | `--strategy taxonomy-guided` | Provides full 7-category taxonomy; LLM diagnoses + fixes |
| Diagnosis-only | `--strategy diagnosis` | Asks for inefficiency analysis, no optimization |
| Hardware-target | `--strategy hardware-target --target x86_avx2` | Targets specific hardware (x86\_avx2, arm\_apple, gpu\_cuda, …) |

### Supported models (configure in `models.yaml`)

| Family | Example IDs | Key |
|---|---|---|
| Claude (Anthropic) | `claude-sonnet-4-6`, `claude-opus-4-6`, `claude-haiku-4-5` | `ANTHROPIC_API_KEY` |
| GPT / o3 (OpenAI) | `gpt-4o`, `gpt-4o-mini`, `o3-mini` | `OPENAI_API_KEY` |
| DeepSeek | `deepseek-v3`, `deepseek-r1` | `DEEPSEEK_API_KEY` |
| Gemini (Google) | `gemini-2-flash`, `gemini-2-pro` | `GOOGLE_API_KEY` |
| Llama 3.1/3.2/3.3 (Meta) | `llama-3.1-70b-together`, `llama-3.1-8b-groq` | `TOGETHER_API_KEY` / `GROQ_API_KEY` |
| Mistral / Mixtral | `mistral-7b-together`, `mixtral-8x7b-groq` | `TOGETHER_API_KEY` / `GROQ_API_KEY` |
| Gemma 2 (Google) | `gemma2-9b-together`, `gemma2-9b-groq` | `TOGETHER_API_KEY` / `GROQ_API_KEY` |
| Phi-3 (Microsoft) | `phi-3-mini-together`, `phi-3-medium-together` | `TOGETHER_API_KEY` |
| Qwen 2.5 (Alibaba) | `qwen2.5-7b-together`, `qwen2.5-72b-together` | `TOGETHER_API_KEY` |
| Falcon | `falcon-7b-together`, `falcon-40b-together` | `TOGETHER_API_KEY` |
| Any of the above (local) | `llama3.1-ollama`, `mistral-ollama`, `phi4-ollama`, … | none — Ollama |

To add a new model, append an entry to `models.yaml` — no code changes needed.

# Project Tree
``` bash
.
├── README.md                     
├── Makefile
│
├── main.c                           
├── harness/
│   └── bench_harness.h              // Timing, verification, reporting utilities
├── patterns/
│   ├── cat1_semantic_redundancy.c   // SR-1 to SR-5  (5 patterns)
│   ├── cat2_input_sensitive.c       // IS-1 to IS-4  (4 patterns)
│   ├── cat3_control_flow.c          // CF-1 to CF-4  (4 patterns)
│   ├── cat4_human_style.c           // HR-1 to HR-5  (5 patterns)
│   ├── cat5_data_structure.c        // DS-1 to DS-4  (4 patterns)
│   ├── cat6_algorithmic.c           // AL-1 to AL-4  (4 patterns)
│   └── cat7_memory_io.c             // MI-1 to MI-4  (4 patterns)
│
├── generate_variants.py             // Generates N slow/fast C pairs per pattern
├── evaluate_llm.py                  // Sends slow code to LLMs, measures output
│
├── scripts/
│   ├── test_variant.py              // Test one generated variant
│   └── batch_test.py                // Test all generated variants
│
└── dataset/                         // Generated output
    ├── index.json                   // Master index of all variants
    ├── index.csv                    // Spreadsheet-friendly index
    └── SR_1/SR-1_v000/
        ├── slow.c                   // Inefficient code
        ├── fast.c                   // Hand-optimized reference
        ├── test.c                   // Test harness (compile + verify)
        └── metadata.json            // Pattern ID, difficulty, description
```

# Commands
```bash
# Generates 30 variants per pattern (7 generators) = 210 total programs
python3 generate_variants.py --patterns all --variants 30 --output dataset/
```