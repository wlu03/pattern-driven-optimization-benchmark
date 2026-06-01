"""filter_non_resistant.py
-------------------------
Move every variant whose measured -O3 speedup falls below its per-pattern
resistance threshold to ``dataset/excluded/`` and regenerate
``dataset/index.{json,csv}`` from the remaining variants. After running
the per-pattern measurement sweep, this leaves the active dataset
guaranteed compiler-resistant under the standard ``-O3 -fno-lto`` regime.

The excluded variants are preserved (not deleted) so they remain
reproducible / analyzable. A summary CSV is written to
``dataset/excluded/EXCLUDED.csv`` recording why each variant was moved.

Usage:
    python3 scripts/filter_non_resistant.py [dataset_dir]

The script reads ``measured_compiler_fixable.csv`` from each pattern
subdirectory (produced by ``scripts/measure_compiler_fixable.py`` per
pattern with ``--workers 1``).
"""
import csv
import glob
import json
import os
import shutil
import sys


def load_measurements(dataset_dir):
    """Return list of {variant_id, pattern_id, speedup_O3, resistant_O3,
    resistance_threshold, src_dir} dicts across all per-pattern CSVs."""
    rows = []
    # The aggregated CSV at dataset/measured_compiler_fixable.csv has the most
    # recent measurements (from the most recent sweep). Per-pattern CSVs in
    # subdirs are usually leftover from per-pattern runs. Prefer aggregated.
    agg = os.path.join(dataset_dir, "measured_compiler_fixable.csv")
    if os.path.exists(agg):
        with open(agg) as f:
            for r in csv.DictReader(f):
                rows.append(r)
        return rows
    # Otherwise stitch per-pattern CSVs.
    for csv_path in glob.glob(os.path.join(dataset_dir, "*",
                                            "measured_compiler_fixable.csv")):
        with open(csv_path) as f:
            for r in csv.DictReader(f):
                rows.append(r)
    return rows


def variant_dir(dataset_dir, variant_id):
    """Map e.g. DS-3_v007 -> dataset/DS_3/DS-3_v007, HO-AL-1_v000 ->
    dataset/held_out/HO_AL/HO-AL-1_v000, COMP_v123 -> dataset/COMP/COMP_v123."""
    pattern_pid = variant_id.rsplit("_v", 1)[0]
    if variant_id.startswith("HO-"):
        # HO-AL-1 -> HO_AL
        cat = pattern_pid.split("-")[1]
        return os.path.join(dataset_dir, "held_out", f"HO_{cat}", variant_id)
    if variant_id.startswith("COMP"):
        return os.path.join(dataset_dir, "COMP", variant_id)
    return os.path.join(dataset_dir, pattern_pid.replace("-", "_"), variant_id)


def main(dataset_dir="dataset"):
    rows = load_measurements(dataset_dir)
    if not rows:
        print(f"No measurements found under {dataset_dir!r}. "
              f"Run scripts/measure_compiler_fixable.py first.")
        sys.exit(1)

    non_resistant = [r for r in rows
                     if r.get("resistant_O3", "").lower() == "false"]
    print(f"Total measured: {len(rows)}")
    print(f"Non-resistant at -O3: {len(non_resistant)}")
    if not non_resistant:
        print("All variants resistant — nothing to filter.")
        return

    excluded_dir = os.path.join(dataset_dir, "excluded")
    os.makedirs(excluded_dir, exist_ok=True)

    moved = []
    for r in non_resistant:
        vid = r["variant_id"]
        src = variant_dir(dataset_dir, vid)
        if not os.path.isdir(src):
            print(f"  WARN: source dir not found for {vid}: {src}")
            continue
        # Preserve directory structure under excluded/ so HO_* and COMP_*
        # don't collide with main-set variants having the same v### number.
        rel = os.path.relpath(src, dataset_dir)
        dst = os.path.join(excluded_dir, rel)
        os.makedirs(os.path.dirname(dst), exist_ok=True)
        if os.path.isdir(dst):
            # Already moved (re-run). Remove the duplicate src.
            shutil.rmtree(src)
        else:
            shutil.move(src, dst)
        moved.append({
            "variant_id": vid,
            "pattern_id": r.get("pattern_id"),
            "speedup_O3": r.get("speedup_O3"),
            "resistance_threshold": r.get("resistance_threshold"),
            "original_path": rel,
            "excluded_path": os.path.relpath(dst, dataset_dir),
        })
        print(f"  moved {vid}  speedup={r.get('speedup_O3'):>6}x  "
              f"threshold={r.get('resistance_threshold','?')}  -> {dst}")

    # Rebuild EXCLUDED.csv from the full excluded/ tree, so re-runs of this
    # script accumulate rather than overwriting prior excludes.
    import glob
    all_excluded = []
    for md in glob.glob(os.path.join(excluded_dir, "**", "metadata.json"),
                        recursive=True):
        m = json.load(open(md))
        orig = os.path.relpath(os.path.dirname(md), excluded_dir)
        excl = os.path.relpath(os.path.dirname(md), dataset_dir)
        # Look up speedup from the per-run moved list if present, otherwise
        # leave blank (variant was excluded in a prior run).
        record = next((row for row in moved
                       if row["variant_id"] == m.get("variant_id")), None)
        all_excluded.append({
            "variant_id": m.get("variant_id"),
            "pattern_id": m.get("pattern_id"),
            "speedup_O3": record["speedup_O3"] if record else "",
            "resistance_threshold": (record["resistance_threshold"]
                                     if record else ""),
            "original_path": orig,
            "excluded_path": excl,
        })
    all_excluded.sort(key=lambda r: r["variant_id"])

    excl_csv = os.path.join(excluded_dir, "EXCLUDED.csv")
    with open(excl_csv, "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(all_excluded[0].keys()))
        w.writeheader()
        for row in all_excluded:
            w.writerow(row)
    print(f"\nWrote {excl_csv} ({len(all_excluded)} variants total; "
          f"{len(moved)} new this run)")

    # Regenerate dataset/index.{json,csv} from remaining variants
    print("\nRegenerating dataset/index.{json,csv}...")
    remaining = []
    for md_path in glob.glob(os.path.join(dataset_dir, "**",
                                           "metadata.json"), recursive=True):
        if "excluded" in md_path.split(os.sep):
            continue
        try:
            remaining.append(json.load(open(md_path)))
        except Exception as e:
            print(f"  WARN: failed to parse {md_path}: {e}")

    remaining.sort(key=lambda m: m.get("variant_id", ""))

    idx_json = os.path.join(dataset_dir, "index.json")
    with open(idx_json, "w") as f:
        json.dump(remaining, f, indent=2)
    idx_csv = os.path.join(dataset_dir, "index.csv")
    fieldnames = ["pattern_id", "variant_id", "category", "pattern_name",
                  "variant_desc", "dtype", "difficulty", "compiler_fixable",
                  "num_loops", "num_arrays", "lines_of_code",
                  "expected_speedup_range"]
    with open(idx_csv, "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=fieldnames, extrasaction="ignore")
        w.writeheader()
        for m in remaining:
            w.writerow(m)

    print(f"  index.json: {len(remaining)} variants")
    print(f"  index.csv:  {len(remaining)} variants")


if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else "dataset")
