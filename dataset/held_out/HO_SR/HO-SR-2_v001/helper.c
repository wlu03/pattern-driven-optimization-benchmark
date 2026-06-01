#include <stdint.h>

// Strong avalanche-quality hash matching xxh3 / SipHash-style internal
// structure: many multiply-shift-xor rounds.  noinline + in a separate
// TU so the compiler cannot CSE or inline-vectorize-across-calls when
// invoked from the slow hash table loop.  This mirrors a typical
// std::hash<uint64_t> + SipHash-style mixer used in defensive
// implementations (e.g. Abseil flat_hash_map's default hasher).
__attribute__((noinline))
uint64_t ho_sr2_xxh3_hash_v001(uint64_t k) {
    uint64_t h = k ^ 0x9e3779b97f4a7c15ull;
    // 12 rounds of mix.  Each round: multiply + shift-xor + add.
    for (int r = 0; r < 6; r++) {
        h *= 0xbf58476d1ce4e5b9ull;
        h ^= h >> 30;
        h += 0x9e3779b97f4a7c15ull;
        h *= 0x94d049bb133111ebull;
        h ^= h >> 27;
        h += 0xc6bc279692b5c323ull;
    }
    return h;
}
