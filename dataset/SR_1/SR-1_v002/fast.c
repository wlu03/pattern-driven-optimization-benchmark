double expensive_sr1_v002(int key);

void fast_sr1_v002(double *arr, int n, int key) {
    double f0 = expensive_sr1_v002(key);
    for (int i = 0; i < n; i++) {
        arr[i] *= f0;
    }
}