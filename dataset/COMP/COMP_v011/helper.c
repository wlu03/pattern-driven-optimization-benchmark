#include <math.h>
__attribute__((noinline, noclone))
float config_val_v011(int key) {
    float r = 0;
    for (int i = 0; i < 100; i++) r += (float)sin((double)(key+i));
    return r;
}