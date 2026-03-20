double soa_accumulate_ds4_v002(double *cb, double *cg, int n);

double fast_ds4_v002(double *cb, double *cg, int n) {
    return soa_accumulate_ds4_v002(cb, cg, n);
}