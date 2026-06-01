int slow_comp_v427(int *sorted_arr, int n, int *queries, int m) {
    int hits = 0;
    for (int q = 0; q < m; q++) {
        int target = queries[q];
        int found = -1;
        for (int i = 0; i < n; i++) {
            int v = sorted_arr[i];
            int cmp;
            /* branchy comparator: emits three different paths */
            if (v < target) cmp = -1;
            else if (v > target) cmp = 1;
            else cmp = 0;
            if (cmp == 0) { found = i; break; }
            if (cmp > 0) break;
        }
        if (found >= 0) hits++;
    }
    return hits;
}