#include <math.h>
double config_val_v048(int key) {
    double r = 0.0;
    for (int i = 0; i < 100; i++) r += sin((double)(key+i));
    return r;
}
double slow_comp_v048(double *arr, int n, int key) {
    double sum = 0.0;
    for (int i = 0; i < n; i++) {
        // Pattern HR-4: Redundant checks
        if (arr == NULL) continue;
        if (n <= 0) break;
        if (i < 0 || i >= n) continue;
        // Pattern SR-4: Invariant function call
        double factor = config_val_v048(key);
        sum += arr[i] * factor;
    }
    return sum;
}