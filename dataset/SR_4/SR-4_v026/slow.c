double expensive_fn_v026(int key) {
    double r = 1.0;
    for (int i = 0; i < 100; i++) {
        r = exp(-fabs(r * 0.01)) + (double)(key % (i+1));
    }
    return r;
}

void slow_sr4_v026(double *arr, int n, int key0, int key1, int key2, int key3) {
    int i = 0;
    while (i < n) {
        double f0 = expensive_fn_v026(key0);
        double f1 = expensive_fn_v026(key1);
        double f2 = expensive_fn_v026(key2);
        double f3 = expensive_fn_v026(key3);
        arr[i] *= f0 * f1 * f2 * f3;
        i++;
    }
}