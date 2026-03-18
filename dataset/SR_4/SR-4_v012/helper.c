#include <math.h>
__attribute__((noinline, noclone))
double expensive_fn_v012(int key) {
    double x = (double)key * 0.001;
    double r = 0.0;
    for (int i = 0; i < 50; i++) {
        r += x * x * x - 3.0 * x * x + 2.0 * x - 1.0;
        x += 0.0001;
    }
    return r;
}