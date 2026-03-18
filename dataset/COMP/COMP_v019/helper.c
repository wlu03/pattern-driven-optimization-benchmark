#include <math.h>
__attribute__((noinline, noclone))
double config_val_v019(int key) {
    double r = 0;
    for (int i = 0; i < 100; i++) r += (double)sin((double)(key+i));
    return r;
}