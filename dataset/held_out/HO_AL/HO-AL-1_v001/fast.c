#include <stdlib.h>

// Partial Fisher-Yates ("selection sampling"): only the last k swaps
// of the full shuffle are needed if we copy from positions n-k..n-1.
// This is a valid uniform k-sample (Knuth, Algorithm S variant), using
// O(k) rand() calls and O(k) swaps instead of O(n).
void fast_ho_al1_v001(int *arr, int n, int k, unsigned int seed, int *out) {
    srand(seed);
    // Only the last k iterations of Fisher-Yates: pick a random element
    // for each of the last k positions of the array.
    for (int i = n - 1; i >= n - k; i--) {
        int j = rand() % (i + 1);
        int t = arr[i]; arr[i] = arr[j]; arr[j] = t;
    }
    for (int i = 0; i < k; i++) out[i] = arr[n - k + i];
}
