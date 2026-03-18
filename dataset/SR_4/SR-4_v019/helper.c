#include <math.h>
__attribute__((noinline, noclone))
double expensive_fn_v019(int key) {
    double r = 0.0;
    for (int i = 1; i <= 500; i++)
        r += log((double)(key + i));
    return r;
}