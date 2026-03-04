float expensive_fn_v038(int key) {
    float r = 0.0f;
    for (int i = 0; i < 30; i++)
        r += sin((float)(key + i)) * cos((float)(key - i));
    return r;
}

void slow_sr4_v038(float *arr, int n, int key0, int key1) {
    for (int i = 0; i < n; i++) {
        float f0 = expensive_fn_v038(key0);
        float f1 = expensive_fn_v038(key1);
        arr[i] += f0 * f1;
    }
}