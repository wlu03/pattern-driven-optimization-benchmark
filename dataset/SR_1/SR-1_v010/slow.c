float expensive_sr1_v010(int key);

void slow_sr1_v010(float *arr, int n, int key0, int key1, int key2, int key3) {
    for (int i = 0; i < n; i++) {
        float f0 = expensive_sr1_v010(key0);
        float f1 = expensive_sr1_v010(key1);
        float f2 = expensive_sr1_v010(key2);
        float f3 = expensive_sr1_v010(key3);
        arr[i] *= f0 * f1 * f2 * f3;
    }
}