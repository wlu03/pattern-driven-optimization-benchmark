#include <math.h>
__attribute__((noinline, noclone))
int compute_v007(int key) {
    int r = 0;
    for (int i = 0; i < 50; i++) r += (int)sin((double)(key+i));
    return r;
}