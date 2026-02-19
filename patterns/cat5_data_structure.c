//Wrong or suboptimal data structure choice leading to performance degradation. Requires semantic understanding of access patterns
#include "../harness/bench_harness.h"
#define N 5000000

// DS-1: Linear Search vs. Hash Lookup
// Using O(n) linear scan when data could be pre-indexed.
// Compiler cannot change data structures.

// Simple hash table for demonstration
#define HT_SIZE 65536
#define HT_MASK (HT_SIZE - 1)

typedef struct { int key; int value; int occupied; } HTEntry;

int ds1_slow_lookup(int *keys, int *values, int n, int target) {
    // Linear search O(n)
    for (int i = 0; i < n; i++) {
        if (keys[i] == target) return values[i];
    }
    return -1;
}

void ds1_build_ht(HTEntry *ht, int *keys, int *values, int n) {
    memset(ht, 0, HT_SIZE * sizeof(HTEntry));
    for (int i = 0; i < n; i++) {
        int h = (unsigned int)keys[i] & HT_MASK;
        while (ht[h].occupied) h = (h + 1) & HT_MASK;
        ht[h].key = keys[i];
        ht[h].value = values[i];
        ht[h].occupied = 1;
    }
}

int ds1_fast_lookup(HTEntry *ht, int target) {
    int h = (unsigned int)target & HT_MASK;
    while (ht[h].occupied) {
        if (ht[h].key == target) return ht[h].value;
        h = (h + 1) & HT_MASK;
    }
    return -1;
}

// DS-2: Repeated Allocation vs. Pre-allocation
// Allocating and freeing memory inside a loop instead of
// reusing a pre-allocated buffer.
void ds2_slow(double *results, double *input, int n, int chunk_size) {
    for (int i = 0; i < n; i += chunk_size) {
        int sz = (i + chunk_size <= n) ? chunk_size : (n - i);
        double *temp = malloc(sz * sizeof(double));  // Alloc per chunk
        for (int j = 0; j < sz; j++) {
            temp[j] = input[i + j] * input[i + j];
        }
        double sum = 0.0;
        for (int j = 0; j < sz; j++) sum += temp[j];
        results[i / chunk_size] = sum;
        free(temp);  // Free per chunk
    }
}

void ds2_fast(double *results, double *input, int n, int chunk_size) {
    double *temp = malloc(chunk_size * sizeof(double));  // Alloc once
    for (int i = 0; i < n; i += chunk_size) {
        int sz = (i + chunk_size <= n) ? chunk_size : (n - i);
        for (int j = 0; j < sz; j++) {
            temp[j] = input[i + j] * input[i + j];
        }
        double sum = 0.0;
        for (int j = 0; j < sz; j++) sum += temp[j];
        results[i / chunk_size] = sum;
    }
    free(temp);
}

// DS-3: Unnecessary Copying (pass-by-value semantics)
// Copying entire arrays/structs when only a reference is needed.
typedef struct {
    double data[64];  // 512 bytes
    int size;
} BigStruct;

double ds3_slow_process(BigStruct s) {
    // Entire struct copied onto stack
    double sum = 0.0;
    for (int i = 0; i < s.size; i++) sum += s.data[i];
    return sum;
}

double ds3_fast_process(const BigStruct *s) {
    // Only pointer passed
    double sum = 0.0;
    for (int i = 0; i < s->size; i++) sum += s->data[i];
    return sum;
}


// DS-4: Cache-Unfriendly Access Patterns (AoS vs SoA)
// Array of Structures causes cache thrashing when only one
// field is accessed. Structure of Arrays is cache-friendly.

// AoS: Array of Structures
typedef struct {
    double x, y, z;     // Position
    double vx, vy, vz;  // Velocity
    double mass;
    double charge;       // 64 bytes total
} Particle_AoS;

// SoA: Structure of Arrays
typedef struct {
    double *x, *y, *z;
    double *vx, *vy, *vz;
    double *mass;
    double *charge;
} Particles_SoA;

double ds4_slow_total_mass(Particle_AoS *particles, int n) {
    // Accesses only `mass` but loads entire 64-byte struct per cache line
    double total = 0.0;
    for (int i = 0; i < n; i++) {
        total += particles[i].mass;  // Stride of 64 bytes
    }
    return total;
}

double ds4_fast_total_mass(Particles_SoA *particles, int n) {
    // Dense access: only mass array, 8-byte stride
    double total = 0.0;
    for (int i = 0; i < n; i++) {
        total += particles->mass[i];
    }
    return total;
}

void run_data_structure(void) {

    srand(42);
    // DS-1: Linear vs Hash lookup
    {
        int n_keys = 50000;
        int n_queries = 100000;
        int *keys = malloc(n_keys * sizeof(int));
        int *values = malloc(n_keys * sizeof(int));
        int *queries = malloc(n_queries * sizeof(int));

        for (int i = 0; i < n_keys; i++) {
            keys[i] = i * 7 + 13;
            values[i] = i * 3;
        }
        for (int i = 0; i < n_queries; i++) {
            queries[i] = keys[rand() % n_keys];
        }

        HTEntry *ht = malloc(HT_SIZE * sizeof(HTEntry));
        ds1_build_ht(ht, keys, values, n_keys);

        BenchTimer t;
        int sum_slow = 0, sum_fast = 0;

        timer_start(&t);
        for (int i = 0; i < 1000; i++)  // Fewer queries for linear search
            sum_slow += ds1_slow_lookup(keys, values, n_keys, queries[i]);
        double ms_slow = timer_stop(&t);

        timer_start(&t);
        for (int i = 0; i < 1000; i++)
            sum_fast += ds1_fast_lookup(ht, queries[i]);
        double ms_fast = timer_stop(&t);

        int ok = (sum_slow == sum_fast);
        record_result("DS-1", "Linear Search vs Hash Lookup", ms_slow, ms_fast, ok);
        printf("[DS-1] Slow=%.2fms Fast=%.2fms Speedup=%.2fx %s\n",
               ms_slow, ms_fast, ms_slow/ms_fast, ok ? "PASS" : "FAIL");

        free(keys); free(values); free(queries); free(ht);
    }

    // DS-2: Repeated allocation
    {
        int chunk = 1024;
        int n_results = N / chunk + 1;
        double *input = malloc(N * sizeof(double));
        double *res_slow = malloc(n_results * sizeof(double));
        double *res_fast = malloc(n_results * sizeof(double));
        fill_random_double(input, N, -10.0, 10.0);

        BenchTimer t;
        timer_start(&t);
        ds2_slow(res_slow, input, N, chunk);
        double ms_slow = timer_stop(&t);

        timer_start(&t);
        ds2_fast(res_fast, input, N, chunk);
        double ms_fast = timer_stop(&t);

        int ok = verify_array_double(res_slow, res_fast, n_results, 1e-9);
        record_result("DS-2", "Repeated Allocation vs Pre-alloc", ms_slow, ms_fast, ok);
        printf("[DS-2] Slow=%.2fms Fast=%.2fms Speedup=%.2fx %s\n",
               ms_slow, ms_fast, ms_slow/ms_fast, ok ? "PASS" : "FAIL");

        free(input); free(res_slow); free(res_fast);
    }

    // DS-3: Struct copying
    {
        int n_structs = 2000000;
        BigStruct *arr = malloc(n_structs * sizeof(BigStruct));
        for (int i = 0; i < n_structs; i++) {
            arr[i].size = 64;
            for (int j = 0; j < 64; j++) arr[i].data[j] = (double)(i + j);
        }

        BenchTimer t;
        double sum_slow = 0, sum_fast = 0;

        timer_start(&t);
        for (int i = 0; i < n_structs; i++) sum_slow += ds3_slow_process(arr[i]);
        double ms_slow = timer_stop(&t);

        timer_start(&t);
        for (int i = 0; i < n_structs; i++) sum_fast += ds3_fast_process(&arr[i]);
        double ms_fast = timer_stop(&t);

        int ok = verify_double(sum_slow, sum_fast, 1e-6);
        record_result("DS-3", "Unnecessary Copying (by-value)", ms_slow, ms_fast, ok);
        printf("[DS-3] Slow=%.2fms Fast=%.2fms Speedup=%.2fx %s\n",
               ms_slow, ms_fast, ms_slow/ms_fast, ok ? "PASS" : "FAIL");

        free(arr);
    }

    // DS-4: AoS vs SoA
    {
        int np = N;
        Particle_AoS *aos = malloc(np * sizeof(Particle_AoS));
        Particles_SoA soa;
        soa.mass = malloc(np * sizeof(double));

        for (int i = 0; i < np; i++) {
            aos[i].mass = (double)(i % 100) * 0.1;
            soa.mass[i] = aos[i].mass;
        }

        BenchTimer t;
        double r_slow, r_fast;

        timer_start(&t);
        for (int r = 0; r < 5; r++) r_slow = ds4_slow_total_mass(aos, np);
        double ms_slow = timer_stop(&t) / 5.0;

        timer_start(&t);
        for (int r = 0; r < 5; r++) r_fast = ds4_fast_total_mass(&soa, np);
        double ms_fast = timer_stop(&t) / 5.0;

        int ok = verify_double(r_slow, r_fast, 1e-6);
        record_result("DS-4", "Cache-Unfriendly Access (AoS vs SoA)", ms_slow, ms_fast, ok);
        printf("[DS-4] Slow=%.2fms Fast=%.2fms Speedup=%.2fx %s\n",
               ms_slow, ms_fast, ms_slow/ms_fast, ok ? "PASS" : "FAIL");

        free(aos); free(soa.mass);
    }
}
