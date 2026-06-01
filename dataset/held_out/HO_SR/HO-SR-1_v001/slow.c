// Slow: every call recomputes expensive_query_ho_sr1_v001(key).  The
// query is in a separate TU + noinline so the compiler cannot CSE it
// across calls to slow_ho_sr1_v001 or hoist it out of the test loop.
extern int expensive_query_ho_sr1_v001(int k);

long long slow_ho_sr1_v001(int *arr, int n, int key) {
    int q = expensive_query_ho_sr1_v001(key);
    long long sum = 0;
    for (int i = 0; i < n; i++) sum += (long long)arr[i] + q;
    return sum;
}
