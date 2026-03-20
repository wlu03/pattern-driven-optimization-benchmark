#include <math.h>

__attribute__((noinline))
double expensive_sr1_v009(int key) {
    double r = fabs((double)key) + 1.0;
    for (int i = 0; i < 50; i++) r = sqrt(r + (double)i);
    return r;
}
