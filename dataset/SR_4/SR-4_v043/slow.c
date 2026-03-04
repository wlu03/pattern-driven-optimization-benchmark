double expensive_fn_v043(int key) {
    double r = 0.0;
    for (int i = 1; i <= 500; i++)
        r += log((double)(key + i));
    return r;
}

void slow_sr4_v043(double *arr, int n, int key0, int key1) {
    int i = 0;
    while (i < n) {
        double f0 = expensive_fn_v043(key0);
        double f1 = expensive_fn_v043(key1);
        arr[i] *= f0 * f1;
        i++;
    }
}