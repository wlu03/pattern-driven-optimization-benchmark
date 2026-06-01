int slow_comp_v693(int *raw, int *n_valid, int *valid_indices, int n_chunks, int chunk_size) {
    int *scratch = (int*)malloc(chunk_size * sizeof(int));
    int acc = 0;
    for (int c = 0; c < n_chunks; c++) {
        /* fixed-size memcpy: copy the whole chunk regardless of n_valid */
        memcpy(scratch, raw + c * chunk_size, chunk_size * sizeof(int));
        int nv = n_valid[c];
        for (int k = 0; k < nv; k++) {
            int idx = valid_indices[c * chunk_size + k];
            acc += scratch[idx];
        }
    }
    free(scratch);
    return acc;
}