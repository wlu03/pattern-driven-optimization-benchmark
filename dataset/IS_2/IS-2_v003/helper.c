#include <math.h>

__attribute__((noinline))
double is2_expensive_v003(double val, double thr){
    volatile double vval = val;
    volatile double vthr = thr;
    double sign = (vval >= 0) ? (double)1.0 : (double)-1.0;
    double vabs = (double)fabs((double)vval);
    double result;
    if(vabs > vthr){
        result = sign*((volatile double)1.0*(1.0+(double)exp((double)(vabs-(volatile double)1.0)-1.0)));
    } else {
        result = vval;
    }
    volatile double vresult = result;
    return (double)vresult;
}
