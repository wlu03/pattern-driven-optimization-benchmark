#include <stdio.h>
#include <stdlib.h>
#include <math.h>
#include <string.h>

__attribute__((noinline))
float fn_relu_v024(float x);
float fn_square_v024(float x);
float fn_scale_v024(float x);
float fn_negate_v024(float x);

void fast_cf4_v024(float *out, float *in, int n, float (*fn)(float)) {
    if      (fn == fn_relu_v024)   { for (int i=0;i<n;i++) out[i]=in[i]>(float)0?in[i]:(float)0; }
    else if (fn == fn_square_v024) { for (int i=0;i<n;i++) out[i]=in[i]*in[i]; }
    else if (fn == fn_scale_v024)  { for (int i=0;i<n;i++) out[i]=in[i]*(float)1.5; }
    else if (fn == fn_negate_v024) { for (int i=0;i<n;i++) out[i]=-in[i]; }
    else                            { for (int i=0;i<n;i++) out[i]=fn(in[i]); }
}
float fn_relu_v024(float x)   { return x > (float)0 ? x : (float)0; }
float fn_square_v024(float x) { return x * x; }
float fn_scale_v024(float x)  { return x * (float)1.5; }
float fn_negate_v024(float x) { return -x; }