float expensive_fn_v032(int key) {
    float r = 1.0f;
    for (int i = 0; i < 200; i++) {
        r = exp(-fabs(r * 0.01f)) + (float)(key % (i+1));
    }
    return r;
}

void slow_sr4_v032(float *arr, int n, int key0, int key1) {
    int i = 0;
    while (i < n) {
        float f0 = expensive_fn_v032(key0);
        float f1 = expensive_fn_v032(key1);
        arr[i] *= f0 * f1;
        i++;
    }
}