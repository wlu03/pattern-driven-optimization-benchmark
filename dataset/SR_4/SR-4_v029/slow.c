float expensive_fn_v029(int key) {
    float base = 1.0f + (float)(key % 10) * 0.01f;
    float r = base;
    for (int i = 0; i < 1000; i++) r = pow(base, r * 0.01f);
    return r;
}

void slow_sr4_v029(float *arr, int n, int key0, int key1, int key2, int key3) {
    int i = 0;
    while (i < n) {
        float f0 = expensive_fn_v029(key0);
        float f1 = expensive_fn_v029(key1);
        float f2 = expensive_fn_v029(key2);
        float f3 = expensive_fn_v029(key3);
        arr[i] *= f0 * f1 * f2 * f3;
        i++;
    }
}