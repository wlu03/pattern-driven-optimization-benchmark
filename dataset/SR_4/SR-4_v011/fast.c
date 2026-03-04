void fast_sr4_v011(double *arr, int n, int key0, int key1) {
    double f0 = expensive_fn_v011(key0);
    double f1 = expensive_fn_v011(key1);
    for (int i = 0; i < n; i++) {
        arr[i] *= f0 * f1;
    }
}