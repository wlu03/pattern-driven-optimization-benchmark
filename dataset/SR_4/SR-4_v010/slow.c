double expensive_fn_v010(int key) {
    double r = 1.0;
    for (int i = 0; i < 500; i++) {
        r = exp(-fabs(r * 0.01)) + (double)(key % (i+1));
    }
    return r;
}

void slow_sr4_v010(double *arr, int n, int key0, int key1, int key2, int key3) {
    for (int i = 0; i < n; i++) {
        double f0 = expensive_fn_v010(key0);
        double f1 = expensive_fn_v010(key1);
        double f2 = expensive_fn_v010(key2);
        double f3 = expensive_fn_v010(key3);
        arr[i] *= f0 * f1 * f2 * f3;
    }
}