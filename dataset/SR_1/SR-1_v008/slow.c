float expensive_sr1_v008(int key);

void slow_sr1_v008(float *arr, int n, int key0, int key1, int key2) {
    int i = 0;
    while (i < n) {
        float f0 = expensive_sr1_v008(key0);
        float f1 = expensive_sr1_v008(key1);
        float f2 = expensive_sr1_v008(key2);
        arr[i] *= f0 * f1 * f2;
        i++;
    }
}