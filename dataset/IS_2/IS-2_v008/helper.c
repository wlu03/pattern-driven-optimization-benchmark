#include <math.h>

__attribute__((noinline))
double is2_expensive_v008(double val, double thr){
    volatile double vval = val;
    volatile double vthr = thr;
    double sign = (vval >= 0) ? (double)1.0 : (double)-1.0;
    double vabs = (double)fabs((double)vval);
    double result;
    if(vabs > vthr){
        result = sign*((volatile double)0.5+(double)sqrt((double)(vabs-(volatile double)0.5)));
    } else {
        result = vval;
    }
    volatile double vresult = result;
    return (double)vresult;
}
