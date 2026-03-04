void fast_sr4_v017(double *arr, int n, int key0, int key1, int key2) {
    double f0 = expensive_fn_v017(key0);
    double f1 = expensive_fn_v017(key1);
    double f2 = expensive_fn_v017(key2);
    for (int i = 0; i < n; i++) {
        arr[i] += f0 * f1 * f2;
    }
}