double fast_ds4_v003(double *rank, double *timestamp, double *weight, int n) {
    double total_rank = -1e308;
    double total_timestamp = -1e308;
    double total_weight = -1e308;
    int i = 0;
    while (i < n) {
        if (rank[i] > total_rank) total_rank = rank[i];
        if (timestamp[i] > total_timestamp) total_timestamp = timestamp[i];
        if (weight[i] > total_weight) total_weight = weight[i];
        i++;
    }
    return total_rank + total_timestamp + total_weight;
}