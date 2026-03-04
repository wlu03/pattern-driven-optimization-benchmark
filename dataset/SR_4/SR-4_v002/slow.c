double expensive_fn_v002(int key) {
    double r = 0.0;
    for (int i = 0; i < 100; i++)
        r += sin((double)(key + i)) * cos((double)(key - i));
    return r;
}

void slow_sr4_v002(double *arr, int n, int key0, int key1, int key2, int key3) {
    for (int i = 0; i < n; i++) {
        double f0 = expensive_fn_v002(key0);
        double f1 = expensive_fn_v002(key1);
        double f2 = expensive_fn_v002(key2);
        double f3 = expensive_fn_v002(key3);
        arr[i] *= f0 * f1 * f2 * f3;
    }
}