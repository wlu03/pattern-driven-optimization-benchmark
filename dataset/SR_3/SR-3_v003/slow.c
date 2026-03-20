void slow_sr3_v003(int *data, int *result, int n) {
    for (int i = 0; i < n; i++) {
        int sum = 0;
        for (int j = 0; j <= i; j++) sum += data[j];
        result[i] = sum;
    }
}