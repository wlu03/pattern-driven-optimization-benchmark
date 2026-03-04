float expensive_fn_v035(int key) {
    float x = (float)key * 0.001f;
    float r = 0.0f;
    for (int i = 0; i < 500; i++) {
        r += x * x * x - 3.0f * x * x + 2.0f * x - 1.0f;
        x += 0.0001f;
    }
    return r;
}

void slow_sr4_v035(float *arr, int n, int key0, int key1, int key2) {
    for (int i = 0; i < n; i++) {
        float f0 = expensive_fn_v035(key0);
        float f1 = expensive_fn_v035(key1);
        float f2 = expensive_fn_v035(key2);
        arr[i] *= f0 * f1 * f2;
    }
}