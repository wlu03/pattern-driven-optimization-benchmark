int slow_comp_v698(int *keys, int *vals, int n, int *queries, int m) {
    int sum = 0;
    for (int q = 0; q < m; q++) {
        int target = queries[q];
        for (int i = 0; i < n; i++) {
            if (keys[i] == target) { sum += vals[i]; break; }
        }
    }
    return sum;
}