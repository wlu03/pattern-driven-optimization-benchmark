float slow_comp_v641(int *keys, float *vals, int n, int *queries, int m) {
    float sum = 0;
    for (int q = 0; q < m; q++) {
        int target = queries[q];
        for (int i = 0; i < n; i++) {
            if (keys[i] == target) { sum += vals[i]; break; }
        }
    }
    return sum;
}