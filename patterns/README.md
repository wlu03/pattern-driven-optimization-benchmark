# Patterns

28 hand-written C inefficiency patterns across 7 categories. Each pattern has a `_slow` and `_fast` version. The slow version is correct but sub-optimal in a way that a compiler **cannot** fix — only semantic understanding (or an LLM) can.

---

## Category 1 — Semantic Redundancy (`cat1_semantic_redundancy.c`)

Computations whose redundancy is only visible through algebraic reasoning, not syntax.

| ID | Name | Compiler Difficulty | Inefficiency | Fix |
|---|---|---|---|---|
| SR-1 | Loop-Invariant Function Call (Transcendental Series) | Very High | A log/sin/exp series function is called every iteration with loop-invariant `base` — the transcendental inner loop prevents the compiler from marking it pure/const and hoisting it | Hoist the call: `scale = series_fn(base)` once before the loop, then `arr[i] *= scale` |
| SR-2 | Loop-Invariant Term in Mixed Expression | Very High | `alpha*X[i]*X[i] + beta*Y[i] + penalty(alpha,beta)` — `penalty` has a sin×exp inner loop with loop-invariant args; compiler cannot hoist it | Separate accumulators for data terms; call `penalty` once and multiply by `n`: `alpha*sumXsq + beta*sumY + n*penalty(alpha,beta)` |
| SR-3 | Redundant Aggregation Recomputation | Very High | Running average recomputed from scratch each iteration — O(n²) total | Maintain a running sum: add each element once → O(n) |
| SR-4 | Invariant Function Call in Loop | High | `expensive_config_lookup(config_key)` called every iteration with the same argument — compiler can't hoist across translation-unit boundaries | Hoist the call before the loop; reuse the cached result |
| SR-5 | Repeated Division by Loop-Invariant Denominator | Very High | `out[i] = data[i] / compute_norm(w, m)` — without `restrict`, `out[]` could alias `w[]`, so the compiler cannot prove `compute_norm` is loop-invariant and must re-evaluate it every iteration | Hoist: `inv = 1.0 / compute_norm(w, m)` once before the loop, then `out[i] = data[i] * inv` |

---

## Category 2 — Input-Sensitive Inefficiency (`cat2_input_sensitive.c`)

Performance that depends on runtime data characteristics the compiler cannot observe.

| ID | Name | Compiler Difficulty | Inefficiency | Fix |
|---|---|---|---|---|
| IS-1 | Sparse Data Redundancy | Very High | Weight update `w[k][j] += delta[j]*layer[k]` processes all elements even when 90% are zero | Skip entire rows/columns where `layer[k] == 0` or `delta[j] == 0` |
| IS-2 | Data Distribution Skew | Very High | Expensive gradient clipping (with `log`) applied to every element even though 99% are within threshold | Fast path: `if (fabs(val) <= threshold) { out[i] = val; continue; }` — only compute `log` for the 1% outliers |
| IS-3 | Early Termination | High | Counts all violations to determine if *any* exist — wastes work after the first hit | Return `0` on the first violation found |
| IS-4 | Adaptive Sort (Nearly-Sorted Detection) | Very High | Always runs `qsort` O(n log n) even on nearly-sorted input | Sample 64 random adjacent pairs at runtime; if ≤4 inversions detected, use insertion sort (O(n) on nearly-sorted data) |
| IS-5 | Runtime Alias Check for Restrict Fast-Path | Very High | Compiler must emit conservative aliasing-safe code because it can't prove at compile time that `out`, `A`, `B` don't overlap | Check pointer ranges once at runtime; if non-overlapping (the common case), dispatch to a `__restrict__`-qualified kernel the compiler can freely vectorize |

---

## Category 3 — Control Flow (`cat3_control_flow.c`)

Branches and dispatch patterns that are resolvable at runtime but not compile time.

| ID | Name | Compiler Difficulty | Inefficiency | Fix |
|---|---|---|---|---|
| CF-1 | Data-Uniform Batch Dispatch | Medium | Per-element branch on `type_tags[i]` in a loop where all tags are identical at runtime — prevents vectorization | Scan once for uniformity; route to a tag-specific branch-free loop |
| CF-2 | Hot/Cold Path Separation | Medium | Rare error-handling branch (`flags[i]`, ~1% set) interleaved with hot computation — kills vectorization of the common case | Two-pass: one clean vectorizable pass for all elements, then a sparse fixup pass for flagged indices |
| CF-3 | Vectorization-Hostile Conditional | Medium | `if (in[i] > 0.0)` inside the loop is always true for the given data — the conditional blocks auto-vectorization | Verify the property once (`all_pos` scan), then use a branch-free loop the compiler can vectorize |
| CF-4 | Function Pointer Dispatch in Hot Loop | Medium | Indirect call through `t->fn(in[i])` — one indirect branch per element, no inlining possible | Identify the concrete function pointer at runtime once, then dispatch to a direct inlined loop |

---

## Category 4 — Human-Style Antipatterns (`cat4_human_style.c`)

Inefficiencies introduced by common coding habits, defensive programming, and incremental development.

| ID | Name | Compiler Difficulty | Inefficiency | Fix |
|---|---|---|---|---|
| HR-1 | Redundant Temporary Variables | Low | `temp1 → temp2 → temp3 → result → out[i]` — extra variables force memory writes and hinder register allocation | Inline: `out[i] = (A[i] + B[i]) * C[i] + 1.0` |
| HR-2 | Copy-Paste Duplication | Medium | Four separate passes over data (mean X, mean Y, var X, var Y) from copy-pasted code blocks | Two passes: one for both means, one for both variances |
| HR-3 | Dead / Debug Code | High | `volatile debug_counter++`, NaN checks, and overflow checks inside a hot loop — `volatile` prevents the compiler from removing them | Strip all debug instrumentation from the production path |
| HR-4 | Overly Defensive Checks | Medium | `arr == NULL`, `n <= 0`, `i < 0 || i >= n`, and per-element NaN checks inside a loop that already guarantees they're false | Check once before the loop; remove all redundant per-iteration guards |
| HR-5 | Append Anti-pattern | Low | Capacity check (`if (pos < n)`) and sign guard (`if (val >= 0)`) inside a loop where both are always true | Direct indexed write: `out[i] = A[i] + B[i]` |

---

## Category 5 — Data Structure (`cat5_data_structure.c`)

Wrong or sub-optimal data structure choice that requires understanding the access pattern.

| ID | Name | Compiler Difficulty | Inefficiency | Fix |
|---|---|---|---|---|
| DS-1 | Linear Search vs Hash Lookup | Very High | O(n) linear scan through 50 000-entry array for each of 100 000 queries | Pre-build an open-addressing hash table; each lookup is O(1) |
| DS-2 | Repeated Allocation vs Pre-allocation | High | `malloc` / `free` per chunk inside the processing loop | Allocate the temp buffer once before the loop; reuse it |
| DS-3 | Unnecessary Copying (pass-by-value) | Medium | 512-byte `BigStruct` copied onto the stack for every call to the processing function | Pass by `const *` — only the pointer is copied |
| DS-4 | AoS vs SoA Cache Access | Very High | Array-of-Structures layout means accessing only `mass` loads an entire 64-byte struct per cache line (8× waste) | Structure-of-Arrays: `mass[]` is a dense array with 8-byte stride, filling every cache line |

---

## Category 6 — Algorithmic (`cat6_algorithmic.c`)

Correct but asymptotically sub-optimal algorithms. Compilers cannot change algorithms.

| ID | Name | Compiler Difficulty | Inefficiency | Fix |
|---|---|---|---|---|
| AL-1 | Brute Force vs Memoization/DP | Very High | Recursive Fibonacci — O(2ⁿ) due to recomputed subproblems | Iterative DP with two variables — O(n) |
| AL-2 | Repeated Sort vs Sorted Insertion | Very High | Re-`qsort` the entire array after every insertion — O(n² log n) total | Binary-search for the insertion point, `memmove` to make room — O(n²) total but with much smaller constant |
| AL-3 | Naive vs KMP Pattern Matching | High | O(n×m) brute-force search for a pattern in a text | Knuth-Morris-Pratt: build failure function in O(m), then scan in O(n) |
| AL-4 | Recursive vs DP (Grid Paths) | Very High | Exponential recursive path counting — recomputes overlapping sub-grids | O(r×c) DP table (O(c) space) — no redundant recomputation |

---

## Category 7 — Memory / IO (`cat7_memory_io.c`)

Wasteful memory operations and allocation patterns in hot loops.

| ID | Name | Compiler Difficulty | Inefficiency | Fix |
|---|---|---|---|---|
| MI-1 | Allocation in Loop vs Sliding Window | High | `malloc` / `free` for a window-sized buffer on every iteration of a moving-average loop | Sliding window: maintain a running sum, add the entering element and subtract the leaving one — no allocation needed |
| MI-2 | Redundant Memory Zeroing | Medium | `memset(output, 0, ...)` followed immediately by a loop that overwrites every element | Remove the `memset` — the subsequent write makes it unnecessary |
| MI-3 | Heap Alloc in Hot Loop | High | `malloc(4 * sizeof(double))` for a tiny 4-element scratch buffer every iteration | Use direct arithmetic or a stack array — zero allocation overhead |
| MI-4 | Column-Major vs Row-Major Access | Medium | Outer loop over columns, inner loop over rows in a row-major C array — cache-line stride is `cols × 8` bytes | Swap loop order: outer over rows, inner over columns — sequential 8-byte stride, full cache-line utilisation |

---

## Compiler difficulty scale

| Level | Meaning |
|---|---|
| Low | Compiler can sometimes fix this at `-O2`/`-O3` |
| Medium | Compiler may fix it under ideal conditions (single TU, no aliasing) |
| High | Compiler rarely fixes it — requires cross-TU analysis or semantic knowledge |
| Very High | Compiler cannot fix it — requires runtime data knowledge or algorithm change |
