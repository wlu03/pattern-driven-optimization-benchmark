#ifndef BENCH_HARNESS_H
#define BENCH_HARNESS_H

#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <time.h>
#include <math.h>
#include <float.h>

typedef struct {
    struct timespec start;
    struct timespec end;
    double elapsed_ms;
} BenchTimer;

static inline void timer_start(BenchTimer *t) {
    clock_gettime(CLOCK_MONOTONIC, &t->start);
}

static inline double timer_stop(BenchTimer *t) {
    clock_gettime(CLOCK_MONOTONIC, &t->end);
    t->elapsed_ms = (t->end.tv_sec - t->start.tv_sec) * 1000.0
                   + (t->end.tv_nsec - t->start.tv_nsec) / 1e6;
    return t->elapsed_ms;
}

static inline int verify_double(double a, double b, double tol) {
    if (fabs(a) < 1e-12 && fabs(b) < 1e-12) return 1;
    return fabs(a - b) / fmax(fabs(a), fabs(b)) < tol;
}

static inline int verify_int(int a, int b) {
    return a == b;
}

static inline int verify_array_double(double *a, double *b, int n, double tol) {
    for (int i = 0; i < n; i++) {
        if (!verify_double(a[i], b[i], tol)) {
            fprintf(stderr, "  Mismatch at index %d: %.10f vs %.10f\n", i, a[i], b[i]);
            return 0;
        }
    }
    return 1;
}

static inline int verify_array_int(int *a, int *b, int n) {
    for (int i = 0; i < n; i++) {
        if (a[i] != b[i]) {
            fprintf(stderr, "  Mismatch at index %d: %d vs %d\n", i, a[i], b[i]);
            return 0;
        }
    }
    return 1;
}

// Generator functions for different types of data
static inline void fill_random_double(double *arr, int n, double lo, double hi) {
    for (int i = 0; i < n; i++)
        arr[i] = lo + (hi - lo) * ((double)rand() / RAND_MAX);
}

static inline void fill_random_int(int *arr, int n, int lo, int hi) {
    for (int i = 0; i < n; i++)
        arr[i] = lo + rand() % (hi - lo + 1);
}

static inline void fill_sparse_double(double *arr, int n, double sparsity) {
    for (int i = 0; i < n; i++)
        arr[i] = ((double)rand() / RAND_MAX < sparsity) ? 0.0
                 : -1.0 + 2.0 * ((double)rand() / RAND_MAX);
}

typedef struct {
    const char *category; 
    const char *name;
    double slow_ms;
    double fast_ms;
    double speedup;
    int correct;
} BenchResult;

#define MAX_RESULTS 64
static BenchResult g_results[MAX_RESULTS];
static int g_result_count = 0;

static inline void record_result(const char *cat, const char *name,
                                  double slow_ms, double fast_ms, int correct) {
    BenchResult *r = &g_results[g_result_count++];
    r->category = cat;
    r->name = name;
    r->slow_ms = slow_ms;
    r->fast_ms = fast_ms;
    r->speedup = (fast_ms > 0.001) ? slow_ms / fast_ms : 0.0;
    r->correct = correct;
}

static inline void print_results_table(void) {
    printf("\n%-8s %-45s %10s %10s %8s %8s\n",
           "ID", "Pattern", "Slow(ms)", "Fast(ms)", "Speedup", "Correct");
    printf("──────── ───────────────────────────────────────── "
           "────────── ────────── ──────── ────────\n");
    for (int i = 0; i < g_result_count; i++) {
        BenchResult *r = &g_results[i];
        printf("%-8s %-45s %10.2f %10.2f %7.2fx %8s\n",
               r->category, r->name, r->slow_ms, r->fast_ms,
               r->speedup, r->correct ? "PASS" : "FAIL");
    }
}

#define WARMUP_RUNS 2
#define BENCH_RUNS  5

#define RUN_PATTERN(cat, name, setup_code, slow_code, fast_code, verify_code) \
    do { \
        BenchTimer _t; \
        double _slow_total = 0, _fast_total = 0; \
        setup_code; \
        /* Warmup */ \
        for (int _w = 0; _w < WARMUP_RUNS; _w++) { slow_code; fast_code; } \
        /* Bench slow */ \
        for (int _r = 0; _r < BENCH_RUNS; _r++) { \
            timer_start(&_t); \
            slow_code; \
            timer_stop(&_t); \
            _slow_total += _t.elapsed_ms; \
        } \
        /* Bench fast */ \
        for (int _r = 0; _r < BENCH_RUNS; _r++) { \
            timer_start(&_t); \
            fast_code; \
            timer_stop(&_t); \
            _fast_total += _t.elapsed_ms; \
        } \
        int _correct = (verify_code); \
        record_result(cat, name, _slow_total / BENCH_RUNS, _fast_total / BENCH_RUNS, _correct); \
        printf("[%s] %s: %.2f ms → %.2f ms (%.2fx) %s\n", \
               cat, name, _slow_total / BENCH_RUNS, _fast_total / BENCH_RUNS, \
               (_fast_total > 0.001) ? _slow_total / _fast_total : 0.0, \
               _correct ? "✓" : "✗ INCORRECT"); \
    } while(0)

#endif // BENCH_HARNESS_H
