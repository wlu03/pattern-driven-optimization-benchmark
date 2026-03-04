double expensive_fn_v012(int key) {
    double r = fabs((double)key) + 1.0;
    for (int i = 0; i < 50; i++) r = sqrt(r + (double)i);
    return r;
}

void slow_sr4_v012(double *arr, int n, int key) {
    int i = 0;
    while (i < n) {
        double f0 = expensive_fn_v012(key);
        arr[i] *= f0;
        i++;
    }
}