static double expensive_fn_v004(int key) {
    double r = fabs((double)key) + 1.0;
    for (int i = 0; i < 30; i++) r = sqrt(r + (double)i);
    return r;
}

void fast_sr4_v004(double *arr, int n, int key) {
    double f0 = expensive_fn_v004(key);
    for (int i = 0; i < n; i++) {
        arr[i] *= f0;
    }
}