static float expensive_fn_v010(int key) {
    float base = 1.0f + (float)(key % 10) * 0.01f;
    float r = base;
    for (int i = 0; i < 200; i++) r = pow(base, r * 0.01f);
    return r;
}

void fast_sr4_v010(float *arr, int n, int key) {
    float f0 = expensive_fn_v010(key);
    for (int i = 0; i < n; i++) {
        arr[i] += f0;
    }
}