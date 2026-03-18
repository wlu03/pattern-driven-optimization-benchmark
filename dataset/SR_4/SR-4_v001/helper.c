#include <math.h>
__attribute__((noinline, noclone))
float expensive_fn_v001(int key) {
    float r = 0.0f;
    for (int i = 1; i <= 500; i++)
        r += log((float)(key + i));
    return r;
}