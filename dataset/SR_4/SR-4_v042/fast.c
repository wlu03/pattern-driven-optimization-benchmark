void fast_sr4_v042(double *arr, int n, int key) {
    double f0 = expensive_fn_v042(key);
    for (int i = 0; i < n; i++) {
        arr[i] += f0;
    }
}