void slow_sr3_v047(int *data, int *result, int n) {
    for (int i = 0; i < n; i++) {
        int sum = 0;
        int start = (i >= 32) ? i - 32 + 1 : 0;
        int count = i - start + 1;
        for (int j = start; j <= i; j++) sum += data[j];
        result[i] = sum / count;
    }
}