void fast_sr4_v031(double *arr, int n, int key) {
    double f0 = expensive_fn_v031(key);
    for (int i = 0; i < n; i++) {
        arr[i] += f0;
    }
}