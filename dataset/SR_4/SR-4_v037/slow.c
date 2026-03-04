double expensive_fn_v037(int key) {
    double x = (double)key * 0.001;
    double r = 0.0;
    for (int i = 0; i < 50; i++) {
        r += x * x * x - 3.0 * x * x + 2.0 * x - 1.0;
        x += 0.0001;
    }
    return r;
}

void slow_sr4_v037(double *arr, int n, int key) {
    for (int i = 0; i < n; i++) {
        double f0 = expensive_fn_v037(key);
        arr[i] += f0;
    }
}