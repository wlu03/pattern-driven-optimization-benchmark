int fast_comp_v378(int *raw, int *n_valid, int *valid_indices, int n_chunks, int chunk_size) {
    /* shared physical buffer (raw) + per-chunk selection vector — no compaction memcpy */
    int acc = 0;
    for (int c = 0; c < n_chunks; c++) {
        int nv = n_valid[c];
        int *base = raw + c * chunk_size;
        if (nv == 1) {
            /* skip-memcpy fast path: single valid row */
            acc += base[valid_indices[c * chunk_size]];
        } else {
            int *sel = valid_indices + c * chunk_size;
            for (int k = 0; k < nv; k++) acc += base[sel[k]];
        }
    }
    return acc;
}