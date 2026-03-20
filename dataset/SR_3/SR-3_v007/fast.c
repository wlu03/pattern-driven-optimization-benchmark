void fast_sr3_v007(double *data, double *result, int n) {
    double sum = 0.0;
    int i = 0;
    while (i < n) {
        sum += data[i];
        result[i] = sum / (i + 1);
        i++;
    }
}