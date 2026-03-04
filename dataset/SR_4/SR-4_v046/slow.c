double expensive_fn_v046(int key) {
    double x = (double)key * 0.001;
    double r = 0.0;
    for (int i = 0; i < 50; i++) {
        r += x * x * x - 3.0 * x * x + 2.0 * x - 1.0;
        x += 0.0001;
    }
    return r;
}

void slow_sr4_v046(double *arr, int n, int key0, int key1, int key2) {
    int i = 0;
    while (i < n) {
        double f0 = expensive_fn_v046(key0);
        double f1 = expensive_fn_v046(key1);
        double f2 = expensive_fn_v046(key2);
        arr[i] += f0 * f1 * f2;
        i++;
    }
}