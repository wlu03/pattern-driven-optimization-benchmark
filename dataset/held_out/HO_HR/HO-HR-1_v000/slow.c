#include <string.h>
#include <stdlib.h>

// Defensive over-copy: copy input into a scratch buffer, transform via
// the noinline helper, then copy back into the output.  Three full
// memory passes over n floats where one would suffice.
extern void ho_hr1_transform_v000(const float *in, float *out, int n);

void slow_ho_hr1_v000(const float *src, float *dst, int n) {
    float *tmp = malloc((size_t)n * sizeof(float));
    memcpy(tmp, src, (size_t)n * sizeof(float));
    ho_hr1_transform_v000(tmp, tmp, n);
    memcpy(dst, tmp, (size_t)n * sizeof(float));
    free(tmp);
}
