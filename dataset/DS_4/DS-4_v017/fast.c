double fast_ds4_v017(double *light, int n) {
    double total_light = -1e308;
    int i = 0;
    while (i < n) {
        if (light[i] > total_light) total_light = light[i];
        i++;
    }
    return total_light;
}