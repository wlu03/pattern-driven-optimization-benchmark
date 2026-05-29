// 12 (key, value) pairs in two flat 48-byte arrays (1 cache line each).
// Linear scan with fully-knowable trip count -> the loop unrolls, the
// comparisons SIMD-vectorize, and the early-exit branch is predicted.
long long fast_ho_ds2_v000(int *keys, int *values, int n_kv,
                            int *queries, int nq) {
    long long sum = 0;
    for (int i = 0; i < nq; i++) {
        int k = queries[i];
        for (int j = 0; j < n_kv; j++) {
            if (keys[j] == k) { sum += values[j]; break; }
        }
    }
    return sum;
}
