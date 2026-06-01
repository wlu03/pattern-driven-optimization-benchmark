// Tagged-dispatch loop: each iteration looks up which "handler" to run
// via an if/else-if chain over non-contiguous discriminant values.
// The chain is too irregular for the compiler to convert to a switch
// jump-table.  With random tags from 8 distinct values, branch predictor
// is overwhelmed and on average ~4 conditional jumps execute per tag.
typedef struct { int tag; float value; } HoCf1Rec;

double slow_ho_cf1_v004(HoCf1Rec *recs, int n) {
    double acc = 0.0;
    for (int i = 0; i < n; i++) {
        int t = recs[i].tag;
        // Irregular discriminant values prevent switch -> jump-table.
        if      (t == 0x1A) acc += (double)recs[i].value * 1.0;
        else if (t == 0x2C) acc += (double)recs[i].value * 1.5;
        else if (t == 0x37) acc += (double)recs[i].value * 2.0;
        else if (t == 0x41) acc += (double)recs[i].value * 2.5;
        else if (t == 0x58) acc += (double)recs[i].value * 3.0;
        else if (t == 0x6F) acc += (double)recs[i].value * 3.5;
        else if (t == 0x73) acc += (double)recs[i].value * 4.0;
        else if (t == 0x89) acc += (double)recs[i].value * 4.5;
    }
    return acc;
}
