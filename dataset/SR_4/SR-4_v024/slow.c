double expensive_fn_v024(int key) {
    unsigned int h = (unsigned int)key;
    double r = 0.0;
    for (int i = 0; i < 1000; i++) {
        h = h * 2654435761u;
        r += (double)(h & 0xFFFF) / 65536.0;
    }
    return r / 1000;
}

void slow_sr4_v024(double *arr, int n, int key) {
    for (int i = 0; i < n; i++) {
        double f0 = expensive_fn_v024(key);
        arr[i] *= f0;
    }
}