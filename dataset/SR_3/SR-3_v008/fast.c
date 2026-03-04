void fast_sr3_v008(double *data, double *result, int n) {
    result[0] = data[0];
    for (int i = 1; i < n; i++) {
        result[i] = 0.3 * data[i] + (1.0 - 0.3) * result[i-1];
    }
}