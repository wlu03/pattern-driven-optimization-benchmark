#include <math.h>

__attribute__((noinline))
float expensive_sr1_v006(int key) {
    float r = fabs((float)key) + 1.0f;
    for (int i = 0; i < 100; i++) r = sqrt(r + (float)i);
    return r;
}
