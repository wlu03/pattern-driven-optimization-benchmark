void fast_sr3_v012(double *data, double *result, int n) {
    double sum_sq = 0.0;
    for (int i = 0; i < n; i++) {
        sum_sq += data[i] * data[i];
        result[i] = sqrt(sum_sq / (i + 1));
    }
}