double fast_comp_v464(double *val, double *weight, int n) {
    double acc = 0;
    for (int i = 0; i < n; i++) {
        double v = val[i];
        if (v == 0) continue;
        acc += v * weight[i];
    }
    return acc;
}