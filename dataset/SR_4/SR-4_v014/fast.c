static float expensive_fn_v014(int key) {
    float r = 1.0f;
    for (int i = 0; i < 1000; i++) {
        r = exp(-fabs(r * 0.01f)) + (float)(key % (i+1));
    }
    return r;
}

void fast_sr4_v014(float *arr, int n, int key) {
    float f0 = expensive_fn_v014(key);
    for (int i = 0; i < n; i++) {
        arr[i] *= f0;
    }
}