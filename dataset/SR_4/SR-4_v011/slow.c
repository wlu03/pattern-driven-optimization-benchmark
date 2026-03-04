double expensive_fn_v011(int key) {
    double r = 0.0;
    for (int i = 1; i <= 500; i++)
        r += log((double)(key + i));
    return r;
}

void slow_sr4_v011(double *arr, int n, int key0, int key1) {
    for (int i = 0; i < n; i++) {
        double f0 = expensive_fn_v011(key0);
        double f1 = expensive_fn_v011(key1);
        arr[i] *= f0 * f1;
    }
}