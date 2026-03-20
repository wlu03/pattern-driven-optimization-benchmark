void slow_sr3_v012(double *data, double *result, int n) {
    for (int i = 0; i < n; i++) {
        double sum = 0.0;
        for (int j = 0; j <= i; j++) sum += data[j];
        result[i] = sum;
    }
}