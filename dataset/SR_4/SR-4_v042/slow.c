double expensive_fn_v042(int key) {
    double r = 0.0;
    for (int i = 1; i <= 100; i++)
        r += log((double)(key + i));
    return r;
}

void slow_sr4_v042(double *arr, int n, int key) {
    for (int i = 0; i < n; i++) {
        double f0 = expensive_fn_v042(key);
        arr[i] += f0;
    }
}