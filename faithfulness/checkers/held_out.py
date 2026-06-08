"""
held_out.py
-----------
Bespoke structural faithfulness checkers for the held-out (HO-*) patterns.

The held-out set (dataset/held_out/) is a post-2026-05 contamination-defense
wave of 36 *novel* micro-optimization patterns — distinct transformations from
the base 27, so the base-category checkers do not apply. Until these existed,
HO-* rows fell through to `_heldout_fallback_check`, which never returns
``faithful`` and so forced every held-out attempt into the unfaithful column.

Design notes specific to this family:

* These checkers are invoked with ``slow_code == ""`` from
  ``faithfulness/report_2x2.py`` (the held-out slow source is not carried in
  the scored CSVs, exactly as for COMP). So each checker judges the *expected
  optimized shape* from ``model_output`` alone — which is what the per-pattern
  ``fast.c`` reference encodes. ``slow_code`` is used only as a corroborating
  signal when present.
* Detection keys on *algorithm-level* idioms (compiler builtins, magic
  constants, memory layout, loop structure), not on variable names, so a model
  that implements the intended algorithm with its own naming still scores
  faithful.
* Verdicts use the shared ``_result`` scoring: all signals pass -> ``faithful``,
  none -> ``unfaithful``, mixed -> ``partial``. A genuinely equivalent but
  differently-shaped solution lands in FAITHFUL_ALTERNATIVE via the
  equivalence axis of the two-axis cascade, so these checkers aim to identify
  the *intended* transformation rather than to accept any speedup.

Families are added phase by phase; see CHECKERS registration in __init__.py.
"""

import re

from ._base import PatternChecker, _result


def _strip_comments(code: str) -> str:
    code = re.sub(r"//[^\n]*", "", code)
    code = re.sub(r"/\*.*?\*/", "", code, flags=re.DOTALL)
    return code


# ───────────────────────────────────────────────────────────────────────────
# HO-AL — Algorithmic Inefficiency (held-out wave)
# ───────────────────────────────────────────────────────────────────────────

class HOAL1Checker(PatternChecker):
    """HO-AL-1: full Fisher-Yates shuffle-then-take-k -> partial Fisher-Yates.

    Expected shape: the shuffle does O(k) work, not O(n). The hallmark is
    sampling only the last k (or first k) positions — `n - k` appears as a
    loop bound / output offset, or the rand-driven swap loop is bounded by k.
    """
    pattern_id = "HO-AL-1"

    def _regex_check(self, slow_code, model_output):
        out = _strip_comments(model_output)
        passed, failed = [], []

        has_rand = bool(re.search(r"\brand\w*\s*\(", out))
        # Unambiguous partial-sampling structure (NOT the slow path's own
        # `for(i=0;i<k)` output-copy loop): either the output reads from the
        # last-k region `arr[n - k + ...]`, or the rand-swap loop only descends
        # to n-k (`i >= n - k`) instead of to 0.
        take_last_k = bool(re.search(r"\[\s*n\s*-\s*k\b", out))
        shuffle_lower_bound = bool(re.search(r">=?\s*n\s*-\s*k\b", out))
        partial = take_last_k or shuffle_lower_bound
        # Full O(n) Fisher-Yates retained: a loop from n-1 down to i > 0.
        full_shuffle = bool(re.search(r"=\s*n\s*-\s*1\s*;\s*\w+\s*>\s*0\s*;", out))

        if partial and not full_shuffle:
            passed.append("O(k) partial Fisher-Yates (take-last-k / n-k-bounded shuffle)")
        elif full_shuffle:
            failed.append("full O(n) Fisher-Yates shuffle retained")
        else:
            failed.append("no partial (take-last-k) sampling structure")

        if not has_rand:
            # A valid uniform k-sample must still draw randomness.
            failed.append("no rand-based uniform sampling")
        return _result(passed, failed)


class HOAL2Checker(PatternChecker):
    """HO-AL-2: exact distinct-count (chained hash set) -> HyperLogLog sketch.

    Expected shape: probabilistic cardinality estimate using a fixed register
    array, leading/trailing-zero rank, and a harmonic-mean estimator — with no
    O(N) per-key node allocation.
    """
    pattern_id = "HO-AL-2"

    def _regex_check(self, slow_code, model_output):
        out = _strip_comments(model_output)
        passed, failed = [], []

        # Rank = position of first set bit via a count-zeros builtin (the HLL
        # core), or an explicit leading-zero loop.
        rank_builtin = bool(re.search(r"__builtin_(?:ctz|clz)\w*", out))
        # Harmonic-mean estimator: alpha constant or m^2/sum form.
        harmonic = bool(
            "0.7213" in out
            or re.search(r"\bm\s*\*\s*m\s*/\s*\w*sum", out)
            or re.search(r"1\.0\s*/\s*\(?\s*\(?1u?l*\s*<<", out)
        )
        # Fixed-footprint registers: a calloc'd byte/short array, not per-key
        # heap nodes (the slow path mallocs a node per distinct key).
        per_key_node = bool(re.search(r"malloc\s*\(\s*sizeof", out))

        if rank_builtin:
            passed.append("HLL rank via count-zeros builtin")
        else:
            failed.append("no leading/trailing-zero rank computation")
        if harmonic:
            passed.append("harmonic-mean cardinality estimator")
        else:
            failed.append("no harmonic-mean estimator")
        if per_key_node:
            failed.append("per-key heap node allocation retained (not O(1) memory)")
        return _result(passed, failed)


class HOAL3Checker(PatternChecker):
    """HO-AL-3: exact frequency-map (chained hash-map) -> Count-Min Sketch.

    Expected shape: a width x depth counter table, d independent hashes per
    update (one per row), and a min-over-d-rows query — fixed memory, no
    per-key node allocation.
    """
    pattern_id = "HO-AL-3"

    def _regex_check(self, slow_code, model_output):
        out = _strip_comments(model_output)
        passed, failed = [], []

        # Depth dimension: a small inner loop over rows `r < D` (the d hashes),
        # or several distinct multiplicative hash constants (>= 3 odd 64-bit).
        depth_loop = bool(re.search(r"for\s*\([^;]*;[^;{}]*<\s*\w*\b[dD]\w*\b", out))
        hash_consts = len(set(re.findall(r"0x[0-9A-Fa-f]{12,16}U?L*L*", out)))
        multi_hash = depth_loop or hash_consts >= 3
        # Query takes the minimum across rows.
        min_query = bool(re.search(r"\bmin\b", out)
                         or re.search(r"\bbest\b", out)
                         or re.search(r"<\s*best\b", out))
        # 2D sketch indexing: `row * W + h`.
        sketch_idx = bool(re.search(r"\[\s*\w+\s*\*\s*\w+\s*\+\s*\w+\s*\]", out))
        per_key_node = bool(re.search(r"malloc\s*\(\s*sizeof", out))

        if multi_hash:
            passed.append("multiple independent hashes (CMS depth)")
        else:
            failed.append("no multi-row hashing (CMS depth) found")
        if min_query:
            passed.append("min-over-rows query (CMS estimate)")
        else:
            failed.append("no min-over-rows query")
        if sketch_idx and not multi_hash:
            passed.append("2D counter-table indexing")
        if per_key_node:
            failed.append("per-key heap node allocation retained")
        return _result(passed, failed)


class HOAL4Checker(PatternChecker):
    """HO-AL-4: vanilla HLL -> HyperLogLogLog (compressed base+offset, bulking).

    Expected shape: 4-bit packed per-register offsets plus a per-block 8-bit
    base, register value reconstructed as base[blk] + offset[idx], inserts
    batched (bulking) to amortize rebasing.
    """
    pattern_id = "HO-AL-4"

    def _regex_check(self, slow_code, model_output):
        out = _strip_comments(model_output)
        passed, failed = [], []

        # 4-bit nibble packing: pair index `>> 1` with low/high nibble masks.
        nibble_pack = bool(
            re.search(r">>\s*1\b", out)
            and re.search(r"&\s*0x0?[fF]\b", out)
            and re.search(r"<<\s*4\b", out)
        )
        # base + offset reconstruction of the register value.
        base_offset = bool(
            re.search(r"\bbase\s*\[", out)
            and re.search(r"\b(off|offset)\w*\b", out)
        )
        # Bulking: a batch loop / batch buffer (the Karppa-Pagh amortization).
        bulking = bool(
            re.search(r"\b(batch|bulk|BATCH|BULK)\w*\b", out)
            or re.search(r"\b256\b", out) and re.search(r"\bblk\w*\b|\bblock\w*\b", out)
        )
        # Still an HLL underneath (rank builtin).
        rank_builtin = bool(re.search(r"__builtin_(?:ctz|clz)\w*", out))

        if nibble_pack:
            passed.append("4-bit packed offset registers")
        else:
            failed.append("no 4-bit nibble-packed offsets")
        if base_offset:
            passed.append("per-block base + per-register offset layout")
        else:
            failed.append("no base+offset register reconstruction")
        if bulking:
            passed.append("batched (bulking) inserts")
        if not rank_builtin:
            failed.append("no HLL rank computation (count-zeros builtin)")
        return _result(passed, failed)


# ───────────────────────────────────────────────────────────────────────────
# HO-SR — Semantic Redundancy (held-out wave)
# ───────────────────────────────────────────────────────────────────────────

def _ct_barrier_present(out: str) -> bool:
    """A compiler barrier that defends a constant-time scan from -O3's
    branch-introducing rewrite: a `volatile` qualifier, an asm barrier, or the
    __builtin_ct_select / intrinsic family."""
    return bool(
        re.search(r"\bvolatile\b", out)
        or re.search(r"\b__asm__\b|\basm\s+volatile\b|\b__asm\b", out)
        or re.search(r"ct_select|__builtin_ct|_mm_\w+", out)
    )


class HOSR1Checker(PatternChecker):
    """HO-SR-1: recompute-every-call -> static cross-call memoization.

    Expected shape: persistent (function-local `static` or file-scope) storage
    of the last (key, result), guarded by a key-equality check so repeat keys
    skip the expensive cross-TU query.
    """
    pattern_id = "HO-SR-1"

    def _regex_check(self, slow_code, model_output):
        out = _strip_comments(model_output)
        passed, failed = [], []
        has_static = bool(re.search(r"\bstatic\b", out))
        cache_guard = bool(
            re.search(r"cach|memo|last_?key|prev_?key|_cached", out, re.I)
            or re.search(r"==\s*\w*key\b|\bkey\s*==", out)
        )
        if has_static and cache_guard:
            passed.append("static cross-call cache with key-hit guard")
        else:
            if not has_static:
                failed.append("no persistent (static/global) cache across calls")
            if not cache_guard:
                failed.append("no cached-key hit check")
        return _result(passed, failed)


class HOSR2Checker(PatternChecker):
    """HO-SR-2: xxh3-style avalanche -> specialized CRC32 (+ multiply) hash."""
    pattern_id = "HO-SR-2"

    def _regex_check(self, slow_code, model_output):
        out = _strip_comments(model_output)
        passed, failed = [], []
        crc = bool(re.search(r"crc32", out, re.I))
        calls_xxh3 = bool(re.search(r"xxh3", out, re.I))
        # A drastically simpler multiplicative mix replacing the extern avalanche.
        custom_mix = bool(re.search(r"\*\s*0x[0-9a-fA-F]{6,}", out))
        if crc:
            passed.append("CRC32-based specialized integer hash")
        elif custom_mix and not calls_xxh3:
            passed.append("simpler multiplicative hash replacing xxh3 avalanche")
        else:
            failed.append("no specialized hash (xxh3-style avalanche retained)")
        if calls_xxh3 and not crc:
            failed.append("xxh3 avalanche hash still used")
        return _result(passed, failed)


class HOSR3Checker(PatternChecker):
    """HO-SR-3: per-iteration malloc/free of a struct -> stack allocation."""
    pattern_id = "HO-SR-3"

    def _regex_check(self, slow_code, model_output):
        out = _strip_comments(model_output)
        passed, failed = [], []
        has_heap = bool(re.search(r"\b(malloc|calloc|realloc)\s*\(", out))
        if not has_heap:
            passed.append("no per-iteration heap allocation (stack-allocated struct)")
        else:
            failed.append("heap allocation retained (malloc/calloc/realloc present)")
        return _result(passed, failed)


class _HOSRBarrierChecker(PatternChecker):
    """Shared base for the inverted constant-time HO-SR patterns (4/5/6): the
    expected shape is a compiler barrier that keeps -O3 from rewriting the
    masked branchless scan into a secret-dependent branch."""
    _idiom = None  # optional corroborating regex

    def _regex_check(self, slow_code, model_output):
        out = _strip_comments(model_output)
        passed, failed = [], []
        if _ct_barrier_present(out):
            passed.append("compiler barrier (volatile/asm/ct_select) defends the CT scan")
        else:
            failed.append("no compiler barrier — naive masked form is broken by -O3")
        if self._idiom and not re.search(self._idiom, out):
            failed.append("constant-time masking idiom not preserved")
        return _result(passed, failed)


class HOSR4Checker(_HOSRBarrierChecker):
    """HO-SR-4: CT bitmask-OR table scan, defended with a volatile barrier."""
    pattern_id = "HO-SR-4"
    _idiom = r"mask|-\s*\(?\s*\w*cond|\|="


class HOSR5Checker(_HOSRBarrierChecker):
    """HO-SR-5: BearSSL masked conditional-move, defended with a barrier."""
    pattern_id = "HO-SR-5"
    _idiom = r"mask|&\s*~|&\s*m\b"


class HOSR6Checker(_HOSRBarrierChecker):
    """HO-SR-6: Kyber message-bit decode (mask & 1665), defended with a barrier."""
    pattern_id = "HO-SR-6"
    _idiom = r"1665|mask"


class HOSR7Checker(PatternChecker):
    """HO-SR-7: variable-amount shift masked (& 0x3F) to elide GCC's UB guard."""
    pattern_id = "HO-SR-7"

    def _regex_check(self, slow_code, model_output):
        out = _strip_comments(model_output)
        passed, failed = [], []
        shift_mask = bool(
            re.search(r"(<<|>>)\s*\(?[^;)\n]*&\s*0x[0-9a-fA-F]+", out)
            or re.search(r"&\s*0x3[fF]\b|&\s*63\b|&\s*0x1[fF]\b|&\s*31\b", out)
        )
        if shift_mask:
            passed.append("shift amount masked (& 0x3F / & 0x1F) to elide UB guard")
        else:
            failed.append("no shift-amount mask")
        return _result(passed, failed)


# ───────────────────────────────────────────────────────────────────────────
# HO-CF — Control Flow (held-out wave)
# ───────────────────────────────────────────────────────────────────────────

class HOCF1Checker(PatternChecker):
    """HO-CF-1: irregular if/else-if tag chain -> single-load weight lookup table."""
    pattern_id = "HO-CF-1"

    def _regex_check(self, slow_code, model_output):
        out = _strip_comments(model_output)
        passed, failed = [], []
        chain = (len(re.findall(r"==\s*0x[0-9a-fA-F]+", out)) >= 3
                 or len(re.findall(r"\belse\s+if\b", out)) >= 3)
        # A multiplier/lookup table indexed by the tag. Use [^\n] (not [^\]])
        # so nested subscripts like `weight[recs[i].tag & 0xFF]` still match.
        lookup = bool(
            re.search(r"\b(weight|table|lut|mult|map|coef|factor|w)\w*\s*\[", out, re.I)
            or re.search(r"\[[^\n]*\btag\b[^\n]*\]", out)
        )
        if lookup and not chain:
            passed.append("tag-indexed lookup table replaces the if/else chain")
        else:
            if not lookup:
                failed.append("no tag-indexed lookup table")
            if chain:
                failed.append("if/else-if tag chain retained")
        return _result(passed, failed)


class HOCF2Checker(PatternChecker):
    """HO-CF-2: switch-based VM dispatch -> computed-goto (labels-as-values)."""
    pattern_id = "HO-CF-2"

    def _regex_check(self, slow_code, model_output):
        out = _strip_comments(model_output)
        passed, failed = [], []
        # `goto *expr` is unambiguous; `&&label` (label address) is matched only
        # when followed by , } ] (table init) to avoid logical-AND false hits.
        computed_goto = bool(
            re.search(r"goto\s*\*", out)
            or re.search(r"&&\s*[A-Za-z_]\w*\s*[,}\]]", out)
        )
        if computed_goto:
            passed.append("computed-goto threaded dispatch (labels-as-values)")
        else:
            failed.append("no computed-goto dispatch (switch/if retained)")
        return _result(passed, failed)


class HOCF3Checker(PatternChecker):
    """HO-CF-3: fragile branch (cmov-vs-jump) -> explicit branchless mask select."""
    pattern_id = "HO-CF-3"

    def _regex_check(self, slow_code, model_output):
        out = _strip_comments(model_output)
        passed, failed = [], []
        # Hallmark of `(a & mask) | (b & ~mask)`: the complement mask.
        mask_select = bool(
            re.search(r"~\s*\w*mask", out)
            or (re.search(r"\bmask\b", out) and re.search(r"&\s*~", out))
        )
        if mask_select:
            passed.append("branchless mask select (no conditional to mis-lower)")
        else:
            failed.append("no branchless mask formulation")
        return _result(passed, failed)


class HOCF4Checker(PatternChecker):
    """HO-CF-4: per-call EOB-checked bit reader -> inlined wide-load refill."""
    pattern_id = "HO-CF-4"

    def _regex_check(self, slow_code, model_output):
        out = _strip_comments(model_output)
        passed, failed = [], []
        # Inlined refill in the hot loop: a wide 8-byte load OR the byte-shift
        # accumulator (`bitbuf |= ... << bitcount`) — the point is that the
        # refill is inline, not behind a per-call helper with its own EOB check.
        refill_inline = bool(
            re.search(r"memcpy\s*\([^;]*,\s*8\s*\)", out)
            or re.search(r"\(\s*(const\s+)?uint64_t\s*\*\s*\)", out)
            or re.search(r"bit_?buf\s*\|=", out)
            or re.search(r"<<\s*bit_?count", out)
        )
        helper_call = bool(re.search(r"\b(get_?bits|read_?bits)\w*\s*\(", out))
        if refill_inline and not helper_call:
            passed.append("inlined bitstream refill (no per-call EOB check)")
        else:
            if not refill_inline:
                failed.append("no inlined refill logic")
            if helper_call:
                failed.append("per-call bit-reader helper retained")
        return _result(passed, failed)


class HOCF5Checker(PatternChecker):
    """HO-CF-5: nested if/else FSM -> precomputed (state,input) transition table."""
    pattern_id = "HO-CF-5"

    def _regex_check(self, slow_code, model_output):
        out = _strip_comments(model_output)
        passed, failed = [], []
        # A flat `[state * stride + input]` or 2D `[state][input]` table read.
        table_lookup = bool(
            re.search(r"\[\s*\w*state\w*\s*\*", out)
            or re.search(r"\[\s*\w*state\w*\s*\]\s*\[", out)
            or (re.search(r"\btable\w*\s*\[", out, re.I) and re.search(r"\bstate\b", out))
        )
        if table_lookup:
            passed.append("precomputed (state,input) transition-table lookup")
        else:
            failed.append("no transition table (nested if/else FSM retained)")
        return _result(passed, failed)


# ───────────────────────────────────────────────────────────────────────────
# HO-DS — Data Structure Inefficiency (held-out wave)
# ───────────────────────────────────────────────────────────────────────────

class HODS1Checker(PatternChecker):
    """HO-DS-1: 256B AoS record -> hot/cold field separation (SoA hot arrays)."""
    pattern_id = "HO-DS-1"

    def _regex_check(self, slow_code, model_output):
        out = _strip_comments(model_output)
        passed, failed = [], []
        soa = bool(
            re.search(r"\bsoa\b|hot_?a|hot_?b|\bhot\s*\[|\bcold\s*\[", out, re.I)
            or re.search(r"double\s*\*\s*\w*hot", out, re.I)
        )
        aos = bool(re.search(r"\.\s*cold\b|->\s*cold\b|\bHoDs1Record\b|cold\s*\[\s*\d", out))
        if soa and not aos:
            passed.append("hot/cold field separation (SoA hot arrays)")
        else:
            failed.append("no hot/cold split (AoS record retained)")
        return _result(passed, failed)


class HODS2Checker(PatternChecker):
    """HO-DS-2: small open-addressed hash table -> flat linear scan over pairs."""
    pattern_id = "HO-DS-2"

    def _regex_check(self, slow_code, model_output):
        out = _strip_comments(model_output)
        passed, failed = [], []
        # Any modulo bucket placement (or the strong-hash extern) means the
        # model kept a hash table rather than a flat scan.
        hash_used = bool(
            re.search(r"strong_hash|ho_ds2_strong", out, re.I)
            or re.search(r"%\s*\w+", out)
        )
        # Linear scan: a nested loop comparing array[idx] (optionally .field)
        # to the query key. Handles keys_array[j]==k and table[j].key==k.
        linear = bool(
            re.search(r"\[\s*\w+\s*\]\s*(?:\.\s*\w+\s*)?==\s*\w", out)
            and len(re.findall(r"\bfor\b", out)) >= 2
        )
        if not hash_used and linear:
            passed.append("flat linear scan over the key array (no hashing)")
        else:
            if hash_used:
                failed.append("hash table / strong hash retained")
            if not linear:
                failed.append("no linear key scan")
        return _result(passed, failed)


class HODS3Checker(PatternChecker):
    """HO-DS-3: int64 field over [0,255] -> uint8_t array densification."""
    pattern_id = "HO-DS-3"

    def _regex_check(self, slow_code, model_output):
        out = _strip_comments(model_output)
        passed, failed = [], []
        narrow = bool(re.search(r"\b(uint8_t|int8_t|unsigned char)\b", out))
        wide = bool(re.search(r"\bHoDs3Wide\b|int64_t\s+level", out))
        if narrow and not wide:
            passed.append("narrowed integer field (uint8_t densification)")
        else:
            failed.append("wide int64 field retained (no densification)")
        return _result(passed, failed)


class HODS4Checker(PatternChecker):
    """HO-DS-4: tag inside scattered node -> 16-bit tag packed into pointer bits."""
    pattern_id = "HO-DS-4"

    def _regex_check(self, slow_code, model_output):
        out = _strip_comments(model_output)
        passed, failed = [], []
        tagged = bool(
            re.search(r"\buintptr_t\b", out)
            and re.search(r">>\s*(4[0-9]|5[0-9]|16)\b|<<\s*(4[0-9]|5[0-9]|16)\b|0xffff[0-9a-f]*", out, re.I)
        )
        if tagged:
            passed.append("fingerprint packed into pointer bits (uintptr_t tag)")
        else:
            failed.append("no pointer-bit-packed tag (still dereferences node)")
        return _result(passed, failed)


class HODS5Checker(PatternChecker):
    """HO-DS-5: per-block {scale,qs} AoS -> Kx8 interleaved super-block (SIMD)."""
    pattern_id = "HO-DS-5"

    def _regex_check(self, slow_code, model_output):
        out = _strip_comments(model_output)
        passed, failed = [], []
        interleaved = bool(
            re.search(r"scales\s*\[\s*8|qs\s*\[\s*8|\[\s*32\s*\]\s*\[\s*8\s*\]|Block8|Kx8", out, re.I)
            or re.search(r"_mm256|_mm_\w+|vld1|float32x|__m256|vmlaq", out)
        )
        if interleaved:
            passed.append("interleaved Kx8 super-block layout / SIMD dequant")
        else:
            failed.append("no block interleaving (per-block AoS retained)")
        return _result(passed, failed)


class HODS6Checker(PatternChecker):
    """HO-DS-6: one-6bit-value-per-byte -> dense cross-byte 6-bit packing."""
    pattern_id = "HO-DS-6"

    def _regex_check(self, slow_code, model_output):
        out = _strip_comments(model_output)
        passed, failed = [], []
        # idx*6 bit addressing with a cross-byte read masked to 6 bits.
        packed = bool(
            re.search(r"\*\s*6\b", out)
            and re.search(r"&\s*0x3[fF]\b", out)
            and re.search(r">>\s*3\b|>>\s*\w*fb|<<\s*\(?\s*8\s*-", out)
        )
        if packed:
            passed.append("dense 6-bit register packing (cross-byte read)")
        else:
            failed.append("no 6-bit packing (one-byte-per-register retained)")
        return _result(passed, failed)


# ───────────────────────────────────────────────────────────────────────────
# HO-HR — Human-Style Antipatterns (held-out wave)
# ───────────────────────────────────────────────────────────────────────────

class HOHR1Checker(PatternChecker):
    """HO-HR-1: memcpy-in / transform / memcpy-out -> direct transform(src,dst)."""
    pattern_id = "HO-HR-1"

    def _regex_check(self, slow_code, model_output):
        out = _strip_comments(model_output)
        passed, failed = [], []
        copies = len(re.findall(r"\bmemcpy\s*\(", out))
        heap = bool(re.search(r"\b(malloc|calloc|alloca)\s*\(", out))
        if copies == 0 and not heap:
            passed.append("direct transform (no scratch buffer / defensive copy)")
        else:
            if copies:
                failed.append(f"defensive memcpy retained ({copies})")
            if heap:
                failed.append("scratch buffer still allocated")
        return _result(passed, failed)


class HOHR2Checker(PatternChecker):
    """HO-HR-2: empirically-wrong unlikely() hint removed (or corrected)."""
    pattern_id = "HO-HR-2"

    def _regex_check(self, slow_code, model_output):
        out = _strip_comments(model_output)
        passed, failed = [], []
        wrong_hint = bool(
            re.search(r"\bunlikely\s*\(", out)
            or re.search(r"__builtin_expect\s*\([^,]*,\s*0\b", out)
        )
        if not wrong_hint:
            passed.append("misleading unlikely() hint removed")
        else:
            failed.append("wrong unlikely()/__builtin_expect(...,0) retained")
        return _result(passed, failed)


class HOHR3Checker(PatternChecker):
    """HO-HR-3: programmer-supplied BCE contract (__builtin_unreachable/assume)."""
    pattern_id = "HO-HR-3"

    def _regex_check(self, slow_code, model_output):
        out = _strip_comments(model_output)
        passed, failed = [], []
        contract = bool(re.search(r"__builtin_unreachable|__builtin_assume|\b__assume\b", out))
        if contract:
            passed.append("BCE contract supplied (__builtin_unreachable/assume)")
        else:
            failed.append("no programmer-supplied bounds-check-elimination contract")
        return _result(passed, failed)


class HOHR4Checker(PatternChecker):
    """HO-HR-4: per-call noinline byte-read helper -> inlined direct loop."""
    pattern_id = "HO-HR-4"

    def _regex_check(self, slow_code, model_output):
        out = _strip_comments(model_output)
        passed, failed = [], []
        # The antipattern is a per-call noinline byte-reader; the fix inlines
        # the access (index, cursor walk, or *p++) directly in the loop.
        helper = bool(
            re.search(r"\bread_byte\w*\s*\(", out)
            or re.search(r"noinline[^;{]*\bread", out)
        )
        access = bool(
            re.search(r"\bsrc\s*\[|\[\s*i\s*\]|\bcursor\b|\*\s*\w+\s*\+\+", out)
        )
        if not helper and access:
            passed.append("inlined byte access (no per-call read helper)")
        else:
            if helper:
                failed.append("per-call read helper retained")
            if not access:
                failed.append("no inlined byte access")
        return _result(passed, failed)


class HOHR5Checker(PatternChecker):
    """HO-HR-5: per-byte switch -> branchless boolean byte-class math."""
    pattern_id = "HO-HR-5"

    def _regex_check(self, slow_code, model_output):
        out = _strip_comments(model_output)
        passed, failed = [], []
        has_switch = bool(re.search(r"\bswitch\s*\(", out))
        boolean = bool(
            re.search(r"\)\s*[|+]\s*\(", out)
            or re.search(r"\+=\s*\(?[^;\n]*[<=!]=", out)
            or re.search(r"\bneeds\b", out)
        )
        if not has_switch and boolean:
            passed.append("branchless boolean byte-class detection")
        else:
            if has_switch:
                failed.append("per-byte switch retained")
            if not boolean:
                failed.append("no branchless boolean math")
        return _result(passed, failed)


# ───────────────────────────────────────────────────────────────────────────
# HO-IS — Input-Sensitive Inefficiency (held-out wave)
# ───────────────────────────────────────────────────────────────────────────

def _counting_sort_idiom(out: str) -> bool:
    """A histogram indexed by value then emitted in order (counting sort)."""
    return bool(
        re.search(r"\w+\s*\[\s*\w*arr\s*\[", out)          # counts[arr[i]]
        or (re.search(r"\b(count|cnt|hist|bucket|freq)\w*\s*\[", out, re.I)
            and re.search(r"\+\+|\+=\s*1", out))
    )


class HOIS1Checker(PatternChecker):
    """HO-IS-1: comparison qsort -> counting sort for small value range."""
    pattern_id = "HO-IS-1"

    def _regex_check(self, slow_code, model_output):
        out = _strip_comments(model_output)
        passed, failed = [], []
        qsort = bool(re.search(r"\bqsort\s*\(", out))
        counting = _counting_sort_idiom(out)
        if counting and not qsort:
            passed.append("counting sort (histogram by value, no qsort)")
        else:
            if qsort:
                failed.append("qsort retained")
            if not counting:
                failed.append("no counting-sort histogram")
        return _result(passed, failed)


class HOIS2Checker(PatternChecker):
    """HO-IS-2: unconditional qsort -> adaptive multi-tier sort dispatch."""
    pattern_id = "HO-IS-2"

    def _regex_check(self, slow_code, model_output):
        out = _strip_comments(model_output)
        passed, failed = [], []
        counting = _counting_sort_idiom(out)
        sorted_detect = bool(
            re.search(r"sorted|ascend|descend|is_sorted|already", out, re.I)
            or re.search(r"arr\s*\[\s*\w+\s*\]\s*[<>]\s*arr\s*\[", out)
        )
        if counting or sorted_detect:
            passed.append("adaptive dispatch (counting sort / pre-sorted detection)")
        else:
            failed.append("no adaptive dispatch (plain qsort only)")
        return _result(passed, failed)


class HOIS3Checker(PatternChecker):
    """HO-IS-3: per-chunk memcpy compaction -> shared buffer + selection vectors."""
    pattern_id = "HO-IS-3"

    def _regex_check(self, slow_code, model_output):
        out = _strip_comments(model_output)
        passed, failed = [], []
        sel = bool(re.search(r"sel_?vec|selection|\bsel\b|\bindices\b", out, re.I))
        memcpy = bool(re.search(r"\bmemcpy\s*\(", out))
        if sel and not memcpy:
            passed.append("logical compaction via selection vectors (no memcpy)")
        else:
            if memcpy:
                failed.append("per-chunk memcpy compaction retained")
            if not sel:
                failed.append("no selection-vector compaction")
        return _result(passed, failed)


class HOIS4Checker(PatternChecker):
    """HO-IS-4: single-stream Huffman -> 4 interleaved bitstreams for ILP."""
    pattern_id = "HO-IS-4"

    def _regex_check(self, slow_code, model_output):
        out = _strip_comments(model_output)
        passed, failed = [], []
        # >=3 of the 4 parallel stream-state pairs (b0/p0 .. b3/p3) or numbered
        # src/sp stream variables.
        n_streams = sum(
            bool(re.search(rf"\bb{i}\b", out) and re.search(rf"\bp{i}\b|\bsp{i}\b", out))
            for i in range(4)
        )
        scalar_multi = (n_streams >= 3
                        or all(re.search(rf"\bsp{i}\b", out) for i in range(4))
                        or all(re.search(rf"\bsrc{i}\b", out) for i in range(3)))
        # Array-of-state form: per-stream arrays stepped by a 4-iteration loop.
        array_multi = bool(re.search(r"\[\s*4\s*\]", out) and re.search(r"<\s*4\b", out))
        multi = scalar_multi or array_multi
        if multi:
            passed.append("multi-stream interleaved decode (ILP)")
        else:
            failed.append("single-stream decode (no interleaving)")
        return _result(passed, failed)


class HOIS5Checker(PatternChecker):
    """HO-IS-5: conservative SAFETY-margin early-exit -> tightened loop bound."""
    pattern_id = "HO-IS-5"

    def _regex_check(self, slow_code, model_output):
        out = _strip_comments(model_output)
        passed, failed = [], []
        big_margin = bool(
            re.search(r"SAFETY|ilimit\s*=\s*\w+\s*\+", out)
            or re.search(r"src_len\s*-\s*\d{2,}", out)
            or re.search(r"\+\s*(180|50|14)\b", out)
        )
        tightened = bool(
            re.search(r"bitp\s*<\s*44|ilowest|op\s*\+\s*4\s*<=|while\s*\(\s*op", out)
        )
        if tightened and not big_margin:
            passed.append("tightened loop bound (no conservative SAFETY margin)")
        else:
            if big_margin:
                failed.append("conservative SAFETY margin retained")
            if not tightened:
                failed.append("no tightened fast-loop bound")
        return _result(passed, failed)


# ───────────────────────────────────────────────────────────────────────────
# HO-MI — Memory & IO (held-out wave)
# ───────────────────────────────────────────────────────────────────────────

class HOMI1Checker(PatternChecker):
    """HO-MI-1: serial pointer-chase -> indexed traversal + software prefetch."""
    pattern_id = "HO-MI-1"

    def _regex_check(self, slow_code, model_output):
        out = _strip_comments(model_output)
        passed, failed = [], []
        if re.search(r"__builtin_prefetch|_mm_prefetch|\bprefetch\w*\s*\(", out):
            passed.append("software prefetch ahead of the pointer chase")
        else:
            failed.append("no software prefetch")
        return _result(passed, failed)


class HOMI2Checker(PatternChecker):
    """HO-MI-2: serial first-touch init -> parallel first-touch (NUMA-local)."""
    pattern_id = "HO-MI-2"

    def _regex_check(self, slow_code, model_output):
        out = _strip_comments(model_output)
        passed, failed = [], []
        parallel_init = bool(
            re.search(r"#\s*pragma\s+omp\s+parallel", out)
            or re.search(r"first[_-]?touch", out, re.I)
            or re.search(r"\bpthread_create\b", out)
            or re.search(r"parallel_init|parallel_sum_parallel", out)  # selects the parallel helper
        )
        if parallel_init:
            passed.append("parallel first-touch initialization")
        else:
            failed.append("no parallel first-touch init")
        return _result(passed, failed)


class HOMI3Checker(PatternChecker):
    """HO-MI-3: RAW-dependent loop -> 3-way split for vectorization (TSVC s1113)."""
    pattern_id = "HO-MI-3"

    def _regex_check(self, slow_code, model_output):
        out = _strip_comments(model_output)
        passed, failed = [], []
        split_extern = bool(re.search(r"s1113_fast", out))   # selects the split helper
        nfor = len(re.findall(r"\bfor\b", out))
        midpoint = bool(re.search(r"/\s*2\b|\bn2\b|\bmid\b|\bhalf\b|tail_const", out, re.I))
        if split_extern or (nfor >= 2 and midpoint):
            passed.append("loop split around the midpoint (vectorizable parts)")
        else:
            failed.append("no midpoint loop split (scalar RAW chain retained)")
        return _result(passed, failed)


class HOMI4Checker(PatternChecker):
    """HO-MI-4: auto-unroll-reliant Huffman loop -> manual 8x unroll."""
    pattern_id = "HO-MI-4"

    def _regex_check(self, slow_code, model_output):
        out = _strip_comments(model_output)
        passed, failed = [], []
        unroll = bool(
            re.search(r"\bi\s*\+=\s*8\b", out)                       # stride-8 unrolled loop
            or len(re.findall(r"\btable\s*\[", out)) >= 8            # >=8 inlined lookups
            or len(re.findall(r"hm4_step|\bstep\w*\s*\(", out)) >= 4
        )
        if unroll:
            passed.append("manual 8x unrolled decode body")
        else:
            failed.append("no manual unroll (single-symbol loop)")
        return _result(passed, failed)
