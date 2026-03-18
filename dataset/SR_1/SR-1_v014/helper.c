#include <math.h>
__attribute__((noinline, noclone))
float series_fn(float base) {
    float r = 0.0;
    for (int k = 1; k <= 18; k++) r += (float)exp(-base * k * 0.02);
    return r;
}