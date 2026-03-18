#include <math.h>
__attribute__((noinline, noclone))
double is2_clamp_v001(double val, double thresh) {
    double abs_val = fabs((double)val);
    double sign = (val >= (double)0) ? (double)1 : (double)-1;
    return sign * (thresh + sqrt((double)((double)1 + abs_val - thresh + (double)1e-7)));
}