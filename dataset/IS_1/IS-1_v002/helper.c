#include <math.h>
__attribute__((noinline, noclone))
double is1_kernel_v002(double a, double b) {
    return a * (log(fabs(a) + 1.0) + log(fabs(b) + 1.0) * 0.5);
}