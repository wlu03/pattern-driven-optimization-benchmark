double fast_ds4_v001(double *score, double *value, int n) {
    double total_score = 0.0;
    double total_value = 0.0;
    int i = 0;
    while (i < n) {
        total_score += score[i];
        total_value += value[i];
        i++;
    }
    return total_score + total_value;
}