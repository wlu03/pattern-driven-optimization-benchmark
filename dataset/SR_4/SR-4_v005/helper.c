#include <math.h>
__attribute__((noinline, noclone))
double expensive_fn_v005(int key) {
    double r = fabs((double)key) + 1.0;
    for (int i = 0; i < 100; i++) r = sqrt(r + (double)i);
    return r;
}