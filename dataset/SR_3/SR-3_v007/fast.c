void fast_sr3_v007(double *data, double *result, int n) {
    double sum = 0.0;
    for (int i = 0; i < n; i++) {
        sum += data[i];
        result[i] = sum;
    }
}