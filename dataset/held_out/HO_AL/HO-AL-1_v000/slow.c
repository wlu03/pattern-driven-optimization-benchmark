#include <stdlib.h>

// Full Fisher-Yates shuffle of n elements, then take the first k.
// Performs O(n) swaps and O(n) rand() calls even though only k samples
// are wanted.  Each swap touches an essentially random cache line.
void slow_ho_al1_v000(int *arr, int n, int k, unsigned int seed, int *out) {
    srand(seed);
    for (int i = n - 1; i > 0; i--) {
        int j = rand() % (i + 1);
        int t = arr[i]; arr[i] = arr[j]; arr[j] = t;
    }
    for (int i = 0; i < k; i++) out[i] = arr[i];
}
