float expensive_fn_v027(int key) {
    float base = 1.0f + (float)(key % 10) * 0.01f;
    float r = base;
    for (int i = 0; i < 500; i++) r = pow(base, r * 0.01f);
    return r;
}

void slow_sr4_v027(float *arr, int n, int key) {
    for (int i = 0; i < n; i++) {
        float f0 = expensive_fn_v027(key);
        arr[i] += f0;
    }
}