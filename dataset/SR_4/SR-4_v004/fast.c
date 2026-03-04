void fast_sr4_v004(double *arr, int n, int key0, int key1) {
    double f0 = expensive_fn_v004(key0);
    double f1 = expensive_fn_v004(key1);
    for (int i = 0; i < n; i++) {
        arr[i] *= f0 * f1;
    }
}