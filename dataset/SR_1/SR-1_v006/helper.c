#include <math.h>
__attribute__((noinline, noclone))
float series_fn(float base) {
    float r = 0.0;
    for (int k = 1; k <= 46; k++) r += (float)log(base * k + 1.0) / k;
    return r;
}