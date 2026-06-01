double soa_accumulate_ds4_v016(double *age, double *rank, double *timestamp, int n);

double fast_ds4_v016(double *age, double *rank, double *timestamp, int n) {
    return soa_accumulate_ds4_v016(age, rank, timestamp, n);
}