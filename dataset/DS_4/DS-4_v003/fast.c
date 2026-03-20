double fast_ds4_v003(double *score, double *category, double *timestamp, double *value, int n) {
    double total_score = 0.0;
    double total_category = 0.0;
    double total_timestamp = 0.0;
    double total_value = 0.0;
    int i = 0;
    while (i < n) {
        total_score += score[i];
        total_category += category[i];
        total_timestamp += timestamp[i];
        total_value += value[i];
        i++;
    }
    return total_score + total_category + total_timestamp + total_value;
}