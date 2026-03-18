#include <math.h>
__attribute__((noinline, noclone))
float compute_v025(int key) {
    float r = 0;
    for (int i = 0; i < 50; i++) r += (float)sin((double)(key+i));
    return r;
}