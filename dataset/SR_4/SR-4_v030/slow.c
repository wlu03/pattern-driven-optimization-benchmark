double expensive_fn_v030(int key) {
    double base = 1.0 + (double)(key % 10) * 0.01;
    double r = base;
    for (int i = 0; i < 1000; i++) r = pow(base, r * 0.01);
    return r;
}

void slow_sr4_v030(double *arr, int n, int key0, int key1) {
    for (int i = 0; i < n; i++) {
        double f0 = expensive_fn_v030(key0);
        double f1 = expensive_fn_v030(key1);
        arr[i] *= f0 * f1;
    }
}