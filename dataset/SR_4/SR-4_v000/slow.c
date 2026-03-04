float expensive_fn_v000(int key) {
    float x = (float)key * 0.001f;
    float r = 0.0f;
    for (int i = 0; i < 30; i++) {
        r += x * x * x - 3.0f * x * x + 2.0f * x - 1.0f;
        x += 0.0001f;
    }
    return r;
}

void slow_sr4_v000(float *arr, int n, int key0, int key1) {
    int i = 0;
    while (i < n) {
        float f0 = expensive_fn_v000(key0);
        float f1 = expensive_fn_v000(key1);
        arr[i] *= f0 * f1;
        i++;
    }
}