void fast_sr3_v029(double *data, double *result, int n) {
    result[0] = data[0];
    int i = 1;
    while (i < n) {
        result[i] = 0.3 * data[i] + (1.0 - 0.3) * result[i-1];
        i++;
    }
}