#include <math.h>
__attribute__((noinline, noclone))
float series_fn(float base) {
    float r = 0.0;
    for (int k = 1; k <= 43; k++) r += (float)log(k + 1.0) * (float)sin(base * k);
    return r;
}