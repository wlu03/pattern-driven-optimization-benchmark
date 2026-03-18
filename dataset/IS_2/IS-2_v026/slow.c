#include <stdio.h>
#include <stdlib.h>
#include <math.h>
#include <string.h>

__attribute__((noinline))
float is2_clamp_v026(float val, float thresh);
void slow_is2_v026(float *out, float *in, int n, float thresh) {
    for (int i = 0; i < n; i++) {
        float val = in[i];
        float clamped = is2_clamp_v026(val, thresh);   /* always called */
        out[i] = ((float)fabs((double)val) > thresh) ? clamped : val;
    }
}