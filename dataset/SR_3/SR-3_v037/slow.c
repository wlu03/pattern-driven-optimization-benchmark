void slow_sr3_v037(int *data, int *result, int n) {
    for (int i = 0; i < n; i++) {
        int sum = 0;
        int start = (i >= 128) ? i - 128 + 1 : 0;
        for (int j = start; j <= i; j++) sum += data[j];
        result[i] = sum;
    }
}