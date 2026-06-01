float fast_comp_v209(float *val, float *weight, int n) {
    float acc = 0;
    for (int i = 0; i < n; i++) {
        float v = val[i];
        if (v == 0) continue;
        acc += v * weight[i];
    }
    return acc;
}