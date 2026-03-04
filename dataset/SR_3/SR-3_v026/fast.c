void fast_sr3_v026(double *data, double *result, int n) {
    double sum = 0.0;
    for (int i = 0; i < n; i++) {
        sum += data[i];
        if (i >= 64) sum -= data[i - 64];
        result[i] = sum;
    }
}