#include <stdio.h>
#include <stdlib.h>
#include <math.h>
#include <string.h>

__attribute__((noinline))
double fn_relu_v003(double x);
double fn_square_v003(double x);
double fn_scale_v003(double x);
double fn_negate_v003(double x);

void fast_cf4_v003(double *out, double *in, int n, double (*fn)(double)) {
    if      (fn == fn_relu_v003)   { for (int i=0;i<n;i++) out[i]=in[i]>(double)0?in[i]:(double)0; }
    else if (fn == fn_square_v003) { for (int i=0;i<n;i++) out[i]=in[i]*in[i]; }
    else if (fn == fn_scale_v003)  { for (int i=0;i<n;i++) out[i]=in[i]*(double)1.5; }
    else if (fn == fn_negate_v003) { for (int i=0;i<n;i++) out[i]=-in[i]; }
    else                            { for (int i=0;i<n;i++) out[i]=fn(in[i]); }
}
double fn_relu_v003(double x)   { return x > (double)0 ? x : (double)0; }
double fn_square_v003(double x) { return x * x; }
double fn_scale_v003(double x)  { return x * (double)1.5; }
double fn_negate_v003(double x) { return -x; }