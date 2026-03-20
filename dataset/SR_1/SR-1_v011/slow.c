float expensive_sr1_v011(int key);

void slow_sr1_v011(float *arr, int n, int key0, int key1) {
    for (int i = 0; i < n; i++) {
        float f0 = expensive_sr1_v011(key0);
        float f1 = expensive_sr1_v011(key1);
        arr[i] *= f0 * f1;
    }
}