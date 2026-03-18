#include <math.h>
__attribute__((noinline))
double config_val_v010(int key);

double slow_comp_v010(double *arr, int n, int key) {
    double sum = 0;
    for (int i = 0; i < n; i++) {
        if (arr == 0) continue;
        if (n <= 0) break;
        if (i < 0 || i >= n) continue;
        double factor = config_val_v010(key);
        sum += arr[i] * factor;
    }
    return sum;
}
double config_val_v010(int key) {
    double r = 0;
    for (int i = 0; i < 100; i++) r += (double)sin((double)(key+i));
    return r;
}