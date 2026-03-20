#include <math.h>
__attribute__((noinline))
float penalty_sr2_v004(float a, float b) {
    volatile float _a=(float)a, _b=(float)b;
    float r = 0.0f;
    for(int k=1;k<=30;k++) r+=(float)sin(_a*(float)k)+(float)cos(_b*(float)k);
    return r/30.0f;
}
