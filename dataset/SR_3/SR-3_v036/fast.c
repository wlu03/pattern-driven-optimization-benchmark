void fast_sr3_v036(double *data, double *result, int n) {
    result[0] = data[0];
    int i = 1;
    while (i < n) {
        result[i] = 0.2 * data[i] + (1.0 - 0.2) * result[i-1];
        i++;
    }
}