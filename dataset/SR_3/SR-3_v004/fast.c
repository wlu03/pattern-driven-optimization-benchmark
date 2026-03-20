void fast_sr3_v004(int *data, int *result, int n) {
    int sum = 0;
    for (int i = 0; i < n; i++) {
        sum += data[i];
        result[i] = sum / (i + 1);
    }
}