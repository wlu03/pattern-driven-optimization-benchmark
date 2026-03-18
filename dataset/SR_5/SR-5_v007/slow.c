#include <math.h>
float compute_norm(float *w, int m);
__attribute__((noinline))
void slow_sr5_v007(float *out, float *data, int n, float *w, int m) {
    for (int i = 0; i < n; i++)
        out[i] = data[i] / compute_norm(w, m);
}