# Pattern-Driven LLM Code Optimization Benchmark
A benchmark framework for evaluating whether LLMs can optimize code patterns that compilers cannot. Contains 28 hand-written inefficiency patterns across 7 categories, a variant generator to produce hundreds of dataset entries, and an LLM evaluation pipeline to measure optimization quality.

# Starting
```bash
# runs 28 patterns
make run

# genertae a dataset of 200+ variant programs
python3 generate_variants.py --patterns all --variants 30 --output dataset/

# verify the generated dataset (if compiles and is correct)
python3 scripts/batch_test.py dataset/

# evaluate an LLM (dry run to see prompts)
python3 evaluate_llm.py --dry-run --strategy taxonomy-guided

# evaluate an LLM (real run, need api keys)
python3 evaluate_llm.py --model claude-sonnet --strategy pattern-aware --output results.csv
```

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
## Generates 30 variants per pattern (7 generators) = 210 total programs
python3 generate_variants.py --patterns all --variants 30 --output dataset/
```