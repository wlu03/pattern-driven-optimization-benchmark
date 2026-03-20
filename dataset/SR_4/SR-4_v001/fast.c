static float expensive_fn_v001(int key) {
    float r = 1.0f;
    for (int i = 0; i < 500; i++) {
        r = exp(-fabs(r * 0.01f)) + (float)(key % (i+1));
    }
    return r;
}

void fast_sr4_v001(float *arr, int n, int key) {
    float f0 = expensive_fn_v001(key);
    for (int i = 0; i < n; i++) {
        arr[i] *= f0;
    }
}