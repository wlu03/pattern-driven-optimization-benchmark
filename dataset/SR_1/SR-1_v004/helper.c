#include <math.h>

__attribute__((noinline))
float expensive_sr1_v004(int key) {
    float r = 0.0f;
    for (int i = 1; i <= 500; i++)
        r += log((float)(key + i));
    return r;
}
