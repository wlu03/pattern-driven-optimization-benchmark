#include <math.h>

__attribute__((noinline))
double expensive_sr1_v002(int key) {
    double r = 0.0;
    for (int i = 0; i < 30; i++)
        r += sin((double)(key + i)) * cos((double)(key - i));
    return r;
}
