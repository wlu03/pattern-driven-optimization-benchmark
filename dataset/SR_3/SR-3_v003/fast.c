void fast_sr3_v003(int *data, int *result, int n) {
    int sum = 0;
    int i = 0;
    while (i < n) {
        sum += data[i];
        result[i] = sum;
        i++;
    }
}