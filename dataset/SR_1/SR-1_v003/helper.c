#include <math.h>

__attribute__((noinline))
double expensive_sr1_v003(int key) {
    unsigned int h = (unsigned int)key;
    double r = 0.0;
    for (int i = 0; i < 50; i++) {
        h = h * 2654435761u;
        r += (double)(h & 0xFFFF) / 65536.0;
    }
    return r / 50;
}
