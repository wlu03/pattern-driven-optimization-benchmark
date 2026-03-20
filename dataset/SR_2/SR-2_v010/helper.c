#include <math.h>
__attribute__((noinline))
float penalty_sr2_v010(float a, float b) {
    volatile float _a=(float)a, _b=(float)b;
    float r = (float)fabs(_a) + 1.0f;
    for(int k=0;k<20;k++) r = (float)log(r + (float)fabs(_b) + 1.0f);
    return r;
}
