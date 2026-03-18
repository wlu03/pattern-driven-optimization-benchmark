__attribute__((noinline, noclone))
int hr4_valid_v025(double val) {
    return val > (double)-1e30 && val < (double)1e30;
}