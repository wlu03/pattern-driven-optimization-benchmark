static float expensive_fn_v012(int key) {
    float base = 1.0f + (float)(key % 10) * 0.01f;
    float r = base;
    for (int i = 0; i < 50; i++) r = pow(base, r * 0.01f);
    return r;
}

void slow_sr4_v012(float *arr, int n, int key0, int key1) {
    int i = 0;
    while (i < n) {
        float f0 = expensive_fn_v012(key0);
        float f1 = expensive_fn_v012(key1);
        arr[i] *= f0 * f1;
        i++;
    }
}