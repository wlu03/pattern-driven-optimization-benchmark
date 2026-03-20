double soa_accumulate_ds4_v009(double *channel, double *baseline, double *z, int n);

double fast_ds4_v009(double *channel, double *baseline, double *z, int n) {
    return soa_accumulate_ds4_v009(channel, baseline, z, n);
}