float expensive_fn_v034(int key) {
    float r = 0.0f;
    for (int i = 1; i <= 30; i++)
        r += log((float)(key + i));
    return r;
}

void slow_sr4_v034(float *arr, int n, int key0, int key1, int key2) {
    for (int i = 0; i < n; i++) {
        float f0 = expensive_fn_v034(key0);
        float f1 = expensive_fn_v034(key1);
        float f2 = expensive_fn_v034(key2);
        arr[i] += f0 * f1 * f2;
    }
}