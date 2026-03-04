double expensive_fn_v005(int key) {
    double r = 0.0;
    for (int i = 1; i <= 200; i++)
        r += log((double)(key + i));
    return r;
}

void slow_sr4_v005(double *arr, int n, int key0, int key1, int key2, int key3) {
    for (int i = 0; i < n; i++) {
        double f0 = expensive_fn_v005(key0);
        double f1 = expensive_fn_v005(key1);
        double f2 = expensive_fn_v005(key2);
        double f3 = expensive_fn_v005(key3);
        arr[i] *= f0 * f1 * f2 * f3;
    }
}