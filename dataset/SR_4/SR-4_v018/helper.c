#include <math.h>
__attribute__((noinline, noclone))
double expensive_fn_v018(int key) {
    double r = 0.0;
    for (int i = 0; i < 50; i++)
        r += sin((double)(key + i)) * cos((double)(key - i));
    return r;
}