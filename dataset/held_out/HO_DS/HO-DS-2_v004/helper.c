// Multi-round cryptographic-quality mixing function.  Marked noinline +
// placed in a separate TU so the compiler cannot constant-fold or
// vectorize-across-calls when invoked from the slow hash-table loop.
__attribute__((noinline))
unsigned int ho_ds2_strong_hash_v004(int k) {
    unsigned int h = (unsigned int)k;
    for (int r = 0; r < 20; r++) {
        h ^= h >> 16;
        h *= 0x85ebca6bu;
        h ^= h >> 13;
        h *= 0xc2b2ae35u;
        h ^= h >> 16;
        h += 0x9e3779b9u;
    }
    return h;
}
