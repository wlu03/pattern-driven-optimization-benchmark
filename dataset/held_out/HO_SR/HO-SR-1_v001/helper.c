// Heavy noinline function that simulates an "expensive query" (parameter
// sweep, table lookup, etc).  Marked noinline + placed in a separate TU
// so the compiler cannot constant-fold or CSE calls across invocations.
__attribute__((noinline))
int expensive_query_ho_sr1_v001(int k) {
    unsigned int h = (unsigned int)k;
    long long acc = 0;
    for (int i = 0; i < 200; i++) {
        h = h * 2654435761u + 0x9e3779b9u;
        h ^= h >> 13;
        acc += (long long)(h & 0xFFFF);
    }
    return (int)(acc & 0x7FFFFFFF);
}
