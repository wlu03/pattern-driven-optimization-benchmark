#include <math.h>
__attribute__((noinline))
float penalty_sr2_v008(float a, float b) {
    volatile float _a=(float)a, _b=(float)b;
    float r = (float)fabs(_a) + (float)fabs(_b) + 1.0f;
    for(int k=0;k<25;k++) r = (float)sqrt(r) + 0.5f;
    return r;
}
