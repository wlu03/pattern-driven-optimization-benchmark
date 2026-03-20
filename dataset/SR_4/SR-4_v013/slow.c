static double expensive_fn_v013(int key) {
    double r = 0.0;
    for (int i = 0; i < 200; i++)
        r += sin((double)(key + i)) * cos((double)(key - i));
    return r;
}

void slow_sr4_v013(double *arr, int n, int key0, int key1) {
    int i = 0;
    while (i < n) {
        double f0 = expensive_fn_v013(key0);
        double f1 = expensive_fn_v013(key1);
        arr[i] *= f0 * f1;
        i++;
    }
}