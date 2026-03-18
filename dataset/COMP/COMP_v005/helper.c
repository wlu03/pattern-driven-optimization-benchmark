#include <math.h>
__attribute__((noinline, noclone))
int config_val_v005(int key) {
    int r = 0;
    for (int i = 0; i < 100; i++) r += (int)sin((double)(key+i));
    return r;
}