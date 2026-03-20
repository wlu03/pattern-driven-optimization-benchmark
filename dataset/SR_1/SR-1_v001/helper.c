#include <math.h>

__attribute__((noinline))
float expensive_sr1_v001(int key) {
    float r = 1.0f;
    for (int i = 0; i < 200; i++) {
        r = exp(-fabs(r * 0.01f)) + (float)(key % (i+1));
    }
    return r;
}
