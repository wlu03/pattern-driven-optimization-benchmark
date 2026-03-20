static double expensive_fn_v002(int key) {
    double x = (double)key * 0.001;
    double r = 0.0;
    for (int i = 0; i < 500; i++) {
        r += x * x * x - 3.0 * x * x + 2.0 * x - 1.0;
        x += 0.0001;
    }
    return r;
}

void fast_sr4_v002(double *arr, int n, int key0, int key1, int key2) {
    double f0 = expensive_fn_v002(key0);
    double f1 = expensive_fn_v002(key1);
    double f2 = expensive_fn_v002(key2);
    for (int i = 0; i < n; i++) {
        arr[i] *= f0 * f1 * f2;
    }
}