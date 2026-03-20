double soa_accumulate_ds4_v013(double *baseline, double *trigger, double *peak, int n);

double fast_ds4_v013(double *baseline, double *trigger, double *peak, int n) {
    return soa_accumulate_ds4_v013(baseline, trigger, peak, n);
}