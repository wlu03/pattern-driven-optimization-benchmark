int slow_al1_v045(int *grid, int m, int n, int r, int c) {
    if (r == 0 && c == 0) return grid[0];
    if (r < 0 || c < 0) return 999999999;
    int up = slow_al1_v045(grid, m, n, r-1, c);
    int left = slow_al1_v045(grid, m, n, r, c-1);
    int best = (up < left) ? up : left;
    return grid[r * n + c] + best;
}