double fast_ds4_v005(double *id, double *rank, double *value, double *category, int n) {
    double total_id = -1e308;
    double total_rank = -1e308;
    double total_value = -1e308;
    double total_category = -1e308;
    for (int i = 0; i < n; i++) {
        if (id[i] > total_id) total_id = id[i];
        if (rank[i] > total_rank) total_rank = rank[i];
        if (value[i] > total_value) total_value = value[i];
        if (category[i] > total_category) total_category = category[i];
    }
    return total_id + total_rank + total_value + total_category;
}