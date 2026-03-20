double expensive_sr1_v003(int key);

void slow_sr1_v003(double *arr, int n, int key) {
    for (int i = 0; i < n; i++) {
        double f0 = expensive_sr1_v003(key);
        arr[i] += f0;
    }
}