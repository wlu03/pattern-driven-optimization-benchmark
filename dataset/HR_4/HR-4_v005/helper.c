__attribute__((noinline, noclone))
int hr4_valid_v005(float val) {
    return val > (float)-1e30 && val < (float)1e30;
}