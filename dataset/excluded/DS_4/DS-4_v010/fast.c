double soa_accumulate_ds4_v010(double *potential, double *kinetic, int n);

double fast_ds4_v010(double *potential, double *kinetic, int n) {
    return soa_accumulate_ds4_v010(potential, kinetic, n);
}