static double expensive_fn_v011(int key) {
    double r = fabs((double)key) + 1.0;
    for (int i = 0; i < 30; i++) r = sqrt(r + (double)i);
    return r;
}

void fast_sr4_v011(double *arr, int n, int key0, int key1, int key2, int key3) {
    double f0 = expensive_fn_v011(key0);
    double f1 = expensive_fn_v011(key1);
    double f2 = expensive_fn_v011(key2);
    double f3 = expensive_fn_v011(key3);
    for (int i = 0; i < n; i++) {
        arr[i] *= f0 * f1 * f2 * f3;
    }
}