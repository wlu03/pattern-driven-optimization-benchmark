int fast_comp_v323(int *val, int *weight, int n) {
    int acc = 0;
    for (int i = 0; i < n; i++) {
        int v = val[i];
        if (v == 0) continue;
        acc += v * weight[i];
    }
    return acc;
}