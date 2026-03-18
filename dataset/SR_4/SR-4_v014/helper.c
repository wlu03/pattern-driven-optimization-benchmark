#include <math.h>
__attribute__((noinline, noclone))
double expensive_fn_v014(int key) {
    double base = 1.0 + (double)(key % 10) * 0.01;
    double r = base;
    for (int i = 0; i < 30; i++) r = pow(base, r * 0.01);
    return r;
}