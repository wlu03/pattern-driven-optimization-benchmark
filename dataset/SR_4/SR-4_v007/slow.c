float expensive_fn_v007(int key) {
    float base = 1.0f + (float)(key % 10) * 0.01f;
    float r = base;
    for (int i = 0; i < 50; i++) r = pow(base, r * 0.01f);
    return r;
}

void slow_sr4_v007(float *arr, int n, int key) {
    for (int i = 0; i < n; i++) {
        float f0 = expensive_fn_v007(key);
        arr[i] += f0;
    }
}