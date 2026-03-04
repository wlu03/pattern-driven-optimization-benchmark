void fast_sr3_v037(int *data, int *result, int n) {
    int sum = 0;
    int i = 0;
    while (i < n) {
        sum += data[i];
        if (i >= 128) sum -= data[i - 128];
        result[i] = sum;
        i++;
    }
}