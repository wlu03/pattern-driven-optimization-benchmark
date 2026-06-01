float fast_comp_v216(int *keys, float *vals, int n, int *queries, int m) {
    int cap = 1;
    while (cap < n * 2) cap <<= 1;
    int mask = cap - 1;
    int *htab_k = (int*)malloc(cap * sizeof(int));
    float *htab_v = (float*)malloc(cap * sizeof(float));
    for (int i = 0; i < cap; i++) { htab_k[i] = -1; htab_v[i] = 0; }
    for (int i = 0; i < n; i++) {
        unsigned int h = (unsigned int)keys[i] * 2654435761u;
        int idx = (int)(h & (unsigned int)mask);
        while (htab_k[idx] != -1) idx = (idx + 1) & mask;
        htab_k[idx] = keys[i];
        htab_v[idx] = vals[i];
    }
    float sum = 0;
    for (int q = 0; q < m; q++) {
        int target = queries[q];
        unsigned int h = (unsigned int)target * 2654435761u;
        int idx = (int)(h & (unsigned int)mask);
        while (htab_k[idx] != -1) {
            if (htab_k[idx] == target) { sum += htab_v[idx]; break; }
            idx = (idx + 1) & mask;
        }
    }
    free(htab_k); free(htab_v);
    return sum;
}