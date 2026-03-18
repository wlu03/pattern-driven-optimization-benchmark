#include <math.h>
__attribute__((noinline, noclone))
double expensive_fn_v023(int key) {
    double r = 1.0;
    for (int i = 0; i < 1000; i++) {
        r = exp(-fabs(r * 0.01)) + (double)(key % (i+1));
    }
    return r;
}