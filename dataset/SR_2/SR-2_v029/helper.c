#include <math.h>
__attribute__((noinline, noclone))
float penalty(float a, float b) {
    float r = 0.0;
    for (int k = 1; k <= 17; k++) r += (float)sin(a * k) * (float)exp(-b * k * 0.02);
    return r;
}