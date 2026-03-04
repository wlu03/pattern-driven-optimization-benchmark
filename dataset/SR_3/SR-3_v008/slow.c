void slow_sr3_v008(double *data, double *result, int n) {
    for (int i = 0; i < n; i++) {
        double ema = data[0];
        for (int j = 1; j <= i; j++)
            ema = 0.3 * data[j] + (1.0 - 0.3) * ema;
        result[i] = ema;
    }
}