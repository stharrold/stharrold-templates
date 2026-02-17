# SPDX-FileCopyrightText: 2025 stharrold
# SPDX-License-Identifier: Apache-2.0
"""Compare two JSONL bench log files side-by-side.

Usage:
    uv run python -m utils.bench_compare bench_logs/A.jsonl bench_logs/B.jsonl
"""

import json
import sys


def load_bench(path):
    """Load a bench log JSONL file. Returns (header, documents, summary)."""
    header = None
    documents = []
    summary = None

    with open(path, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            record = json.loads(line)
            rtype = record.get("type")
            if rtype == "header":
                header = record
            elif rtype == "summary":
                summary = record
            elif rtype == "document":
                documents.append(record)

    return header, documents, summary


def compare(path_a, path_b):
    """Print side-by-side comparison of two bench logs."""
    header_a, docs_a, summary_a = load_bench(path_a)
    header_b, docs_b, summary_b = load_bench(path_b)

    model_a = (header_a or {}).get("model", "A")
    model_b = (header_b or {}).get("model", "B")

    print(f"\n{'=' * 70}")
    print(f"BENCH COMPARISON: {model_a} vs {model_b}")
    print(f"{'=' * 70}")

    # --- Summary stats ---
    if summary_a and summary_b:
        print(f"\n{'Metric':<30} {model_a:>18} {model_b:>18}")
        print("-" * 70)

        fields = [
            ("Total documents", "total_documents"),
            ("Succeeded", "succeeded"),
            ("Failed", "failed"),
            ("Avg entities/doc", "avg_entities_per_doc"),
            ("Avg decompose time (s)", "avg_decompose_time"),
            ("Total wall time (s)", "total_wall_time"),
        ]
        for label, key in fields:
            va = summary_a.get(key, 0)
            vb = summary_b.get(key, 0)
            if isinstance(va, float):
                print(f"{label:<30} {va:>18.2f} {vb:>18.2f}")
            else:
                print(f"{label:<30} {va:>18} {vb:>18}")

        # Entity type distribution
        types_a = summary_a.get("entity_type_distribution", {})
        types_b = summary_b.get("entity_type_distribution", {})
        all_types = sorted(set(list(types_a.keys()) + list(types_b.keys())))
        if all_types:
            print(f"\n{'Entity Type':<30} {model_a:>18} {model_b:>18}")
            print("-" * 70)
            for t in all_types:
                print(f"  {t:<28} {types_a.get(t, 0):>18} {types_b.get(t, 0):>18}")

    # --- Per-document overlap ---
    map_a = {e["document_id"]: e for e in docs_a}
    map_b = {e["document_id"]: e for e in docs_b}
    common_ids = set(map_a.keys()) & set(map_b.keys())

    if common_ids:
        print(f"\n--- Per-document comparison ({len(common_ids)} common documents) ---")

        # Success disagreements
        a_only_ok = []
        b_only_ok = []
        both_ok = []
        for did in sorted(common_ids):
            ea = map_a[did]
            eb = map_b[did]
            a_ok = ea.get("ok", False)
            b_ok = eb.get("ok", False)
            if a_ok and not b_ok:
                a_only_ok.append(did)
            elif b_ok and not a_ok:
                b_only_ok.append(did)
            elif a_ok and b_ok:
                both_ok.append(did)

        print(f"\nBoth succeeded: {len(both_ok)}")
        if a_only_ok:
            print(f"Only {model_a} succeeded: {len(a_only_ok)}")
            for did in a_only_ok[:5]:
                print(f"  {did}: {map_a[did].get('title', '')[:50]}")
        if b_only_ok:
            print(f"Only {model_b} succeeded: {len(b_only_ok)}")
            for did in b_only_ok[:5]:
                print(f"  {did}: {map_b[did].get('title', '')[:50]}")

        # Entity overlap for common successes
        if both_ok:
            overlap_counts = []
            for did in both_ok:
                names_a = set(n.lower() for n in map_a[did].get("entity_names", []))
                names_b = set(n.lower() for n in map_b[did].get("entity_names", []))
                if names_a or names_b:
                    overlap = len(names_a & names_b) / max(len(names_a | names_b), 1)
                    overlap_counts.append(overlap)

            if overlap_counts:
                avg_overlap = sum(overlap_counts) / len(overlap_counts)
                print(f"\nEntity name overlap (Jaccard): {avg_overlap:.1%} avg across {len(overlap_counts)} documents")

        # Timing comparison
        decompose_a = [map_a[did]["timings"].get("03_decompose", 0) for did in both_ok if "03_decompose" in map_a[did].get("timings", {})]
        decompose_b = [map_b[did]["timings"].get("03_decompose", 0) for did in both_ok if "03_decompose" in map_b[did].get("timings", {})]
        if decompose_a and decompose_b:
            print("\nDecompose time (common documents):")
            print(f"  {model_a}: avg {sum(decompose_a) / len(decompose_a):.1f}s, min {min(decompose_a):.1f}s, max {max(decompose_a):.1f}s")
            print(f"  {model_b}: avg {sum(decompose_b) / len(decompose_b):.1f}s, min {min(decompose_b):.1f}s, max {max(decompose_b):.1f}s")
    else:
        print("\nNo common document IDs found between the two runs.")

    print()


if __name__ == "__main__":
    if len(sys.argv) != 3:
        print("Usage: uv run python -m utils.bench_compare <log_a.jsonl> <log_b.jsonl>")
        sys.exit(1)

    compare(sys.argv[1], sys.argv[2])
