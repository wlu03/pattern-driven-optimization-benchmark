static double expensive_fn_v007(int key) {
    double r = 0.0;
    for (int i = 0; i < 100; i++)
        r += sin((double)(key + i)) * cos((double)(key - i));
    return r;
}

void fast_sr4_v007(double *arr, int n, int key) {
    double f0 = expensive_fn_v007(key);
    int i = 0;
    while (i < n) {
        arr[i] *= f0;
        i++;
    }
}