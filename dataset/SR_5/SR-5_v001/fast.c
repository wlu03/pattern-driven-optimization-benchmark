#include <math.h>
float compute_norm(float *w, int m);
__attribute__((noinline))
void fast_sr5_v001(float *out, float *data, int n, float *w, int m) {
    float inv = (float)1.0 / compute_norm(w, m);
    int i = 0;
    while (i < n) {
        out[i] = data[i] * inv;
        i++;
    }
}