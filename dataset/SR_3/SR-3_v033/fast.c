void fast_sr3_v033(double *data, double *result, int n) {
    double sum = 0.0;
    double sum_sq = 0.0;
    for (int i = 0; i < n; i++) {
        sum += data[i];
        sum_sq += data[i] * data[i];
        double mean = sum / (i + 1);
        result[i] = sum_sq / (i + 1) - mean * mean;
    }
}