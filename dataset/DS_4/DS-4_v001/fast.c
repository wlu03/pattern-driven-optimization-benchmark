double fast_ds4_v001(double *channel, int n) {
    double total_channel = 0.0;
    int i = 0;
    while (i < n) {
        total_channel += channel[i];
        i++;
    }
    return total_channel;
}