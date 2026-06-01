// Pointer-linked list whose nodes are deliberately scattered across a
// large heap arena.  Each `p = p->next` cannot speculatively execute
// past the current node load -> one serialized DRAM round-trip per node.
typedef struct HoMi1Node {
    long value;
    struct HoMi1Node *next;
    char _pad[240];
} HoMi1Node;

long long slow_ho_mi1_v002(HoMi1Node *head, long *next_index, long n) {
    (void)next_index; (void)n;
    long long sum = 0;
    HoMi1Node *p = head;
    while (p) {
        sum += p->value;
        p = p->next;
    }
    return sum;
}
