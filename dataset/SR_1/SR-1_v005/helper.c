#include <math.h>
__attribute__((noinline, noclone))
float series_fn(float base) {
    float r = 0.0;
    for (int k = 1; k <= 49; k++) r += (float)exp(-base * k * 0.05);
    return r;
}