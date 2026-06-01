#include <stdlib.h>
#include <string.h>
#include <pthread.h>

typedef struct {
    double *buf;
    long start;
    long end;
    double partial;
} HoMi2Arg;

static void *formula_fill_worker(void *p) {
    HoMi2Arg *a = (HoMi2Arg *)p;
    for (long i = a->start; i < a->end; i++)
        a->buf[i] = (double)(i & 0xFFFF) * 0.001;
    return NULL;
}

static void *sum_worker(void *p) {
    HoMi2Arg *a = (HoMi2Arg *)p;
    double s = 0.0;
    for (long i = a->start; i < a->end; i++) s += a->buf[i];
    a->partial = s;
    return NULL;
}

// SLOW path: single-thread initializes everything, then a fan-out of
// worker threads each computes its partial sum.  On NUMA boxes every
// worker except the init thread fetches remote DRAM.  Even on
// single-socket the serialized init is a sequential bandwidth cost.
__attribute__((noinline))
double parallel_sum_serial_init_ho_mi2_v004(double *buf, long n, int n_threads) {
    // Phase 1: serial fill (single thread).
    for (long i = 0; i < n; i++) buf[i] = (double)(i & 0xFFFF) * 0.001;

    // Phase 2: parallel sum.
    pthread_t *ts = malloc(n_threads * sizeof(pthread_t));
    HoMi2Arg *args = malloc(n_threads * sizeof(HoMi2Arg));
    long chunk = n / n_threads;
    for (int t = 0; t < n_threads; t++) {
        args[t].buf = buf;
        args[t].start = t * chunk;
        args[t].end   = (t == n_threads - 1) ? n : (t + 1) * chunk;
        args[t].partial = 0.0;
        pthread_create(&ts[t], NULL, sum_worker, &args[t]);
    }
    double total = 0;
    for (int t = 0; t < n_threads; t++) {
        pthread_join(ts[t], NULL);
        total += args[t].partial;
    }
    free(ts); free(args);
    return total;
}

// FAST path: parallel first-touch initialization, then parallel sum
// using the SAME partitioning.  On Linux with first-touch NUMA each
// page lands on its writer thread's node; the subsequent sum is
// node-local.  On single-socket / Apple Silicon, we still benefit from
// parallel zeroing bandwidth.
__attribute__((noinline))
double parallel_sum_parallel_init_ho_mi2_v004(double *buf, long n, int n_threads) {
    pthread_t *ts = malloc(n_threads * sizeof(pthread_t));
    HoMi2Arg *args = malloc(n_threads * sizeof(HoMi2Arg));
    long chunk = n / n_threads;

    // Phase 1: parallel first-touch fill.
    for (int t = 0; t < n_threads; t++) {
        args[t].buf = buf;
        args[t].start = t * chunk;
        args[t].end   = (t == n_threads - 1) ? n : (t + 1) * chunk;
        args[t].partial = 0.0;
        pthread_create(&ts[t], NULL, formula_fill_worker, &args[t]);
    }
    for (int t = 0; t < n_threads; t++) pthread_join(ts[t], NULL);

    // Phase 2: parallel sum (same partitioning -> local reads on NUMA).
    for (int t = 0; t < n_threads; t++) {
        args[t].partial = 0.0;
        pthread_create(&ts[t], NULL, sum_worker, &args[t]);
    }
    double total = 0;
    for (int t = 0; t < n_threads; t++) {
        pthread_join(ts[t], NULL);
        total += args[t].partial;
    }
    free(ts); free(args);
    return total;
}
