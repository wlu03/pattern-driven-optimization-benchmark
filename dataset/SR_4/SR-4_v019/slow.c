double expensive_fn_v019(int key) {
    unsigned int h = (unsigned int)key;
    double r = 0.0;
    for (int i = 0; i < 30; i++) {
        h = h * 2654435761u;
        r += (double)(h & 0xFFFF) / 65536.0;
    }
    return r / 30;
}

void slow_sr4_v019(double *arr, int n, int key0, int key1, int key2) {
    for (int i = 0; i < n; i++) {
        double f0 = expensive_fn_v019(key0);
        double f1 = expensive_fn_v019(key1);
        double f2 = expensive_fn_v019(key2);
        arr[i] *= f0 * f1 * f2;
    }
}