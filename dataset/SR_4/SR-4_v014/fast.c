void fast_sr4_v014(double *arr, int n, int key) {
    double f0 = expensive_fn_v014(key);
    for (int i = 0; i < n; i++) {
        arr[i] += f0;
    }
}