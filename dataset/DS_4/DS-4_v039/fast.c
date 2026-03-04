double fast_ds4_v039(double *value, double *timestamp, double *rank, double *weight, int n) {
    double total_value = 0.0;
    double total_timestamp = 0.0;
    double total_rank = 0.0;
    double total_weight = 0.0;
    for (int i = 0; i < n; i++) {
        total_value += value[i];
        total_timestamp += timestamp[i];
        total_rank += rank[i];
        total_weight += weight[i];
    }
    return total_value + total_timestamp + total_rank + total_weight;
}