#include <math.h>
__attribute__((noinline, noclone))
float expensive_fn_v003(int key) {
    float r = fabs((float)key) + 1.0f;
    for (int i = 0; i < 200; i++) r = sqrt(r + (float)i);
    return r;
}