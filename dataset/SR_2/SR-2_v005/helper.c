#include <math.h>
__attribute__((noinline))
double penalty_sr2_v005(double a, double b) {
    volatile double _a=(double)a, _b=(double)b;
    double r = 0.0;
    for(int k=0;k<40;k++) { r = r*_a*0.1 + _b; r = r*_b*0.1 + _a; }
    return r;
}
