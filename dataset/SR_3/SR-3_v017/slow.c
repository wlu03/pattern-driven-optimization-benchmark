void slow_sr3_v017(double *data, double *result, int n) {
    for (int i = 0; i < n; i++) {
        double mx = data[0];
        for (int j = 1; j <= i; j++) if (data[j] > mx) mx = data[j];
        result[i] = mx;
    }
}