#include <math.h>
float compute_norm(float *w, int m);
__attribute__((noinline))
void slow_sr5_v001(float *out, float *data, int n, float *w, int m) {
    int i = 0;
    while (i < n) {
        out[i] = data[i] / compute_norm(w, m);
        i++;
    }
}