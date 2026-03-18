#include <math.h>
__attribute__((noinline, noclone))
float expensive_fn_v021(int key) {
    float base = 1.0f + (float)(key % 10) * 0.01f;
    float r = base;
    for (int i = 0; i < 500; i++) r = pow(base, r * 0.01f);
    return r;
}