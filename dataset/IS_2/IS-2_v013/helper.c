#include <math.h>

__attribute__((noinline))
float is2_expensive_v013(float val, float thr){
    volatile float vval = val;
    volatile float vthr = thr;
    float sign = (vval >= 0) ? (float)1.0 : (float)-1.0;
    float vabs = (float)fabs((double)vval);
    float result;
    if(vabs > vthr){
        result = sign*((volatile float)0.5+(float)log(1.0+vabs-(volatile float)0.5));
    } else {
        result = vval;
    }
    volatile float vresult = result;
    return (float)vresult;
}
