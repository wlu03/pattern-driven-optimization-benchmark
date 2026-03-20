double expensive_sr1_v003(int key);

void fast_sr1_v003(double *arr, int n, int key) {
    double f0 = expensive_sr1_v003(key);
    for (int i = 0; i < n; i++) {
        arr[i] += f0;
    }
}