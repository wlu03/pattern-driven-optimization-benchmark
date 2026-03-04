float expensive_fn_v015(int key) {
    float base = 1.0f + (float)(key % 10) * 0.01f;
    float r = base;
    for (int i = 0; i < 50; i++) r = pow(base, r * 0.01f);
    return r;
}

void slow_sr4_v015(float *arr, int n, int key0, int key1, int key2, int key3) {
    for (int i = 0; i < n; i++) {
        float f0 = expensive_fn_v015(key0);
        float f1 = expensive_fn_v015(key1);
        float f2 = expensive_fn_v015(key2);
        float f3 = expensive_fn_v015(key3);
        arr[i] *= f0 * f1 * f2 * f3;
    }
}