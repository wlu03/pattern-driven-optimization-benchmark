double soa_accumulate_ds4_v006(double *normal_y, double *emissive, double *normal_x, int n);

double fast_ds4_v006(double *normal_y, double *emissive, double *normal_x, int n) {
    return soa_accumulate_ds4_v006(normal_y, emissive, normal_x, n);
}