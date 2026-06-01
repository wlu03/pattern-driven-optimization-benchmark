// Replace the if/else chain with a single bounded array lookup keyed
// by a tag->weight map.  No branches inside the hot loop; the load is
// well-predicted (tags repeat) and the multiply-add is purely
// data-parallel.
typedef struct { int tag; float value; } HoCf1Rec;

#define HO_CF1_TAG_MAX 256

double fast_ho_cf1_v002(HoCf1Rec *recs, int n) {
    // Build a small lookup table once: tag byte -> multiplier (0.0 for
    // unrecognized tags so they contribute nothing, mirroring the
    // implicit "else: skip" in the slow version).
    static double weight[HO_CF1_TAG_MAX];
    static int _inited = 0;
    if (!_inited) {
        weight[0x1A] = 1.0; weight[0x2C] = 1.5; weight[0x37] = 2.0;
        weight[0x41] = 2.5; weight[0x58] = 3.0; weight[0x6F] = 3.5;
        weight[0x73] = 4.0; weight[0x89] = 4.5;
        _inited = 1;
    }
    double acc = 0.0;
    for (int i = 0; i < n; i++) {
        acc += (double)recs[i].value * weight[recs[i].tag & (HO_CF1_TAG_MAX - 1)];
    }
    return acc;
}
