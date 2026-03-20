#include <math.h>
__attribute__((noinline))
double penalty_sr2_v015(double a, double b) {
    volatile double _a=(double)a, _b=(double)b;
    double r = (double)fabs(_a) + 1.0;
    for(int k=0;k<20;k++) r = (double)log(r + (double)fabs(_b) + 1.0);
    return r;
}
