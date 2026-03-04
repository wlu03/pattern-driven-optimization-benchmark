double expensive_fn_v039(int key) {
    double r = 0.0;
    for (int i = 1; i <= 500; i++)
        r += log((double)(key + i));
    return r;
}

void slow_sr4_v039(double *arr, int n, int key0, int key1, int key2) {
    for (int i = 0; i < n; i++) {
        double f0 = expensive_fn_v039(key0);
        double f1 = expensive_fn_v039(key1);
        double f2 = expensive_fn_v039(key2);
        arr[i] *= f0 * f1 * f2;
    }
}