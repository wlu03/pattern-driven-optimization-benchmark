#include <math.h>
__attribute__((noinline))
double penalty_sr2_v016(double a, double b) {
    volatile double _a=(double)a, _b=(double)b;
    double r = (double)fabs(_a) + (double)fabs(_b) + 1.0;
    for(int k=0;k<25;k++) r = (double)sqrt(r) + 0.5;
    return r;
}
