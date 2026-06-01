int fast_comp_v039(int *sorted_arr, int n, int *queries, int m) {
    int hits = 0;
    for (int q = 0; q < m; q++) {
        int target = queries[q];
        int lo = 0, hi = n;
        while (lo < hi) {
            int mid = (lo + hi) >> 1;
            int v = sorted_arr[mid];
            /* branchless: compute lo/hi using arithmetic on (v<target) */
            int lt = (v < target);
            lo = lt ? (mid + 1) : lo;
            hi = lt ? hi : mid;
        }
        if (lo < n && sorted_arr[lo] == target) hits++;
    }
    return hits;
}