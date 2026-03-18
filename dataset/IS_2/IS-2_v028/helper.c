#include <math.h>
__attribute__((noinline, noclone))
float is2_clamp_v028(float val, float thresh) {
    float abs_val = (float)fabs((double)val);
    float sign = (val >= (float)0) ? (float)1 : (float)-1;
    return sign * (thresh + (float)sqrt((double)((float)1 + abs_val - thresh + (float)1e-7)));
}