CC = gcc
CFLAGS_COMMON = -Wall -Wextra -lm
SRC = main.c

.PHONY: all clean run compare

all: bench_O0 bench_O1 bench_O2 bench_O3

bench_O0: $(SRC)
	$(CC) -O0 $(CFLAGS_COMMON) -o $@ $<

bench_O1: $(SRC)
	$(CC) -O1 $(CFLAGS_COMMON) -o $@ $<

bench_O2: $(SRC)
	$(CC) -O2 $(CFLAGS_COMMON) -o $@ $<

bench_O3: $(SRC)
	$(CC) -O3 $(CFLAGS_COMMON) -o $@ $<

run: all
	@echo "═══ Running at -O0 ═══"
	./bench_O0 > results_O0.txt 2>&1
	@echo "═══ Running at -O2 ═══"
	./bench_O2 > results_O2.txt 2>&1
	@echo "═══ Running at -O3 ═══"
	./bench_O3 > results_O3.txt 2>&1
	@echo "Done. Results saved to results_O0.txt, results_O2.txt, results_O3.txt"

# Compare: does the compiler fix the slow version at -O3?
compare: run
	@echo ""
	@echo "═══════════════════════════════════════════════"
	@echo " Compiler Optimization Analysis"
	@echo " If slow_ms at -O3 ≈ fast_ms at -O0,"
	@echo " the compiler already handles this pattern."
	@echo "═══════════════════════════════════════════════"
	@echo ""
	@echo "── -O0 Results (no optimization) ──"
	@grep "^SR\|^IS\|^CF\|^HR\|^DS\|^AL\|^MI" results_O0.txt || true
	@echo ""
	@echo "── -O3 Results (max optimization) ──"
	@grep "^SR\|^IS\|^CF\|^HR\|^DS\|^AL\|^MI" results_O3.txt || true

# Show prompts for LLM evaluation
prompts:
	python3 evaluate_llm.py --dry-run --strategy generic
	python3 evaluate_llm.py --dry-run --strategy pattern-aware
clean:
	rm -f bench_O0 bench_O1 bench_O2 bench_O3 results_*.txt
