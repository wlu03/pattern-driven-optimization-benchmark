double fast_ds4_v004(double *weight, double *rank, int n) {
    double total_weight = 0.0;
    double total_rank = 0.0;
    for (int i = 0; i < n; i++) {
        total_weight += weight[i];
        total_rank += rank[i];
    }
    return total_weight + total_rank;
}