#include <math.h>
__attribute__((noinline))
int config_val_v028(int key);

int slow_comp_v028(int *arr, int n, int key) {
    int sum = 0;
    for (int i = 0; i < n; i++) {
        if (arr == 0) continue;
        if (n <= 0) break;
        if (i < 0 || i >= n) continue;
        int factor = config_val_v028(key);
        sum += arr[i] * factor;
    }
    return sum;
}
int config_val_v028(int key) {
    int r = 0;
    for (int i = 0; i < 100; i++) r += (int)sin((double)(key+i));
    return r;
}