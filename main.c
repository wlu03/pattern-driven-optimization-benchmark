/*
 * Pattern-Driven Benchmark for Code Optimization
 * Main driver: runs all 7 categories, 28 patterns
 * Compile: gcc -O0 -o bench_O0 main.c -lm // no compiler optimization on GCC
 *          gcc -O2 -o bench_O2 main.c -lm // standard level optimization on GCC (inlining, loop unrolling, constant prop, DCE)
 *          gcc -O3 -o bench_O3 main.c -lm // max compiler optimization including (vectorization, function cloning, loop transformation + O2 stuff)
 * This measures the baseline: how much does the compiler
 * optimize the SLOW versions? Then compare with LLM output.
 */

#include "harness/bench_harness.h"
#include "patterns/cat1_semantic_redundancy.c"
#include "patterns/cat2_input_sensitive.c"
#include "patterns/cat3_control_flow.c"
#include "patterns/cat4_human_style.c"
#include "patterns/cat5_data_structure.c"
#include "patterns/cat6_algorithmic.c"
#include "patterns/cat7_memory_io.c"

int main(int argc, char *argv[]) {
    printf("Pattern Driven Code Optimization Benchmark\n");
    // Run all categories
    run_semantic_redundancy();
    run_input_sensitive();
    run_control_flow();
    run_human_style();
    run_data_structure();
    run_algorithmic();
    run_memory_io(); 

    // Print summary table
    printf("\n");
    print_results_table();

    // Print CSV for analysis
    printf("\n── CSV Output ──\n");
    printf("category,pattern,slow_ms,fast_ms,speedup,correct\n");
    for (int i = 0; i < g_result_count; i++) {
        BenchResult *r = &g_results[i];
        printf("%s,\"%s\",%.4f,%.4f,%.4f,%d\n",
               r->category, r->name, r->slow_ms, r->fast_ms,
               r->speedup, r->correct);
    }

    // Summary stats per category
    printf("\n Category Summary \n");
    const char *cats[] = {"SR", "IS", "CF", "HR", "DS", "AL", "MI"};
    const char *cat_names[] = {
        "Semantic Redundancy", "Input-Sensitive", "Control-Flow",
        "Human-Style", "Data Structure", "Algorithmic", "Memory/IO"
    };

    for (int c = 0; c < 7; c++) {
        double total_speedup = 0.0;
        int count = 0, all_correct = 1;
        for (int i = 0; i < g_result_count; i++) {
            if (strncmp(g_results[i].category, cats[c], 2) == 0) {
                total_speedup += g_results[i].speedup;
                count++;
                if (!g_results[i].correct) all_correct = 0;
            }
        }
        printf("  %-25s: avg speedup = %6.2fx (%d patterns, %s)\n",
               cat_names[c], total_speedup / count, count,
               all_correct ? "all correct" : "SOME INCORRECT");
    }

    return 0;
}
