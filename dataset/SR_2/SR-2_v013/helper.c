#include <math.h>
__attribute__((noinline))
double penalty_sr2_v013(double a, double b) {
    volatile double _a=(double)a, _b=(double)b;
    double r = 0.0;
    for(int k=1;k<=30;k++) r+=(double)sin(_a*(double)k)+(double)cos(_b*(double)k);
    return r/30.0;
}
