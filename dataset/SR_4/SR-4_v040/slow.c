double expensive_fn_v040(int key) {
    double r = 0.0;
    for (int i = 0; i < 500; i++)
        r += sin((double)(key + i)) * cos((double)(key - i));
    return r;
}

void slow_sr4_v040(double *arr, int n, int key0, int key1, int key2, int key3) {
    int i = 0;
    while (i < n) {
        double f0 = expensive_fn_v040(key0);
        double f1 = expensive_fn_v040(key1);
        double f2 = expensive_fn_v040(key2);
        double f3 = expensive_fn_v040(key3);
        arr[i] += f0 * f1 * f2 * f3;
        i++;
    }
}