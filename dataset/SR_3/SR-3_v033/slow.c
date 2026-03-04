void slow_sr3_v033(double *data, double *result, int n) {
    for (int i = 0; i < n; i++) {
        double sum = 0.0;
        for (int j = 0; j <= i; j++) sum += data[j];
        double mean = sum / (i + 1);
        double var_sum = 0.0;
        for (int j = 0; j <= i; j++) {
            double diff = data[j] - mean;
            var_sum += diff * diff;
        }
        result[i] = var_sum / (i + 1);
    }
}