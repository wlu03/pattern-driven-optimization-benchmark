#include <math.h>
__attribute__((noinline, noclone))
float expensive_fn_v027(int key) {
    float base = 1.0f + (float)(key % 10) * 0.01f;
    float r = base;
    for (int i = 0; i < 1000; i++) r = pow(base, r * 0.01f);
    return r;
}