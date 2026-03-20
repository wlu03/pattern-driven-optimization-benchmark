void slow_sr3_v012(double *data, double *result, int n) {
    for (int i = 0; i < n; i++) {
        double sum_sq = 0.0;
        for (int j = 0; j <= i; j++) sum_sq += data[j] * data[j];
        result[i] = sqrt(sum_sq / (i + 1));
    }
}