#include <math.h>

__attribute__((noinline))
float expensive_sr1_v000(int key) {
    unsigned int h = (unsigned int)key;
    float r = 0.0f;
    for (int i = 0; i < 50; i++) {
        h = h * 2654435761u;
        r += (float)(h & 0xFFFF) / 65536.0f;
    }
    return r / 50;
}
