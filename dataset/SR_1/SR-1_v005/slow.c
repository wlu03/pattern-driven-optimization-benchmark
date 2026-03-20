double expensive_sr1_v005(int key);

void slow_sr1_v005(double *arr, int n, int key0, int key1) {
    for (int i = 0; i < n; i++) {
        double f0 = expensive_sr1_v005(key0);
        double f1 = expensive_sr1_v005(key1);
        arr[i] *= f0 * f1;
    }
}