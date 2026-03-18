#include <math.h>
__attribute__((noinline, noclone))
float is1_kernel_v001(float a, float b) {
    return a * (logf(fabsf(a) + 1.0f) + logf(fabsf(b) + 1.0f) * 0.5f);
}