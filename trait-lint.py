#!/usr/bin/env python3
"""
trait-lint — keep the Design Taste Library's trait vocabulary from fragmenting.

    python3 trait-lint.py [--fix]

Checks, in order of how much damage they do:
  ERROR  unknown trait ......... in an entry but nowhere in vocabulary.json
  FIX    alias used ............ resolvable to a canonical trait (--fix rewrites)
  WARN   near-duplicate ........ two canonical traits that likely mean one thing
  WARN   pending promotion ..... pending trait now on 2+ entries
  INFO   singleton ............. canonical trait used exactly once
  INFO   unused ................ canonical trait used zero times
"""

import json
import re
import sys
from itertools import combinations
from pathlib import Path

HERE = Path(__file__).parent
LIBRARY = HERE / "design-taste-library.json"
VOCAB = HERE / "vocabulary.json"

STOPWORDS = {"a", "an", "the", "with", "and", "as", "of", "on", "in", "to", "for", "only", "or"}
NEAR_DUPLICATE_THRESHOLD = 0.5


def normalize(phrase):
    """Lowercase, drop punctuation and stopwords, crudely singularize."""
    words = re.split(r"[^a-z0-9]+", phrase.lower())
    out = set()
    for w in words:
        if not w or w in STOPWORDS:
            continue
        if len(w) > 3 and w.endswith("s") and not w.endswith("ss"):
            w = w[:-1]
        out.add(w)
    return out


def jaccard(a, b):
    if not a or not b:
        return 0.0
    return len(a & b) / len(a | b)


def load():
    if not LIBRARY.exists() or not VOCAB.exists():
        sys.exit(f"missing {LIBRARY.name} or {VOCAB.name} — run from the library folder")
    return json.loads(LIBRARY.read_text()), json.loads(VOCAB.read_text())


def build_lookup(vocab):
    """Map every accepted spelling -> canonical trait id."""
    lookup, traits = {}, {}
    for t in vocab["traits"]:
        traits[t["id"]] = t
        lookup[t["id"]] = t["id"]
        lookup[t["label"].lower()] = t["id"]
        for alias in t.get("aliases", []):
            lookup[alias.lower()] = t["id"]
    return lookup, traits


def main():
    fix = "--fix" in sys.argv
    lib, vocab = load()
    lookup, traits = build_lookup(vocab)
    retired = {r["label"].lower(): r for r in vocab.get("retired", [])}

    errors, fixes, warns, infos = [], [], [], []
    usage = {tid: [] for tid in traits}

    for entry in lib["entries"]:
        eid = entry["id"]
        for i, raw in enumerate(entry.get("traits", [])):
            key = raw.lower()
            tid = lookup.get(key)

            if tid is None:
                if key in retired:
                    errors.append(
                        f"{eid}: '{raw}' was retired — {retired[key]['reason']}"
                    )
                else:
                    close = [
                        traits[c]["label"]
                        for c in traits
                        if jaccard(normalize(raw), normalize(traits[c]["label"])) >= NEAR_DUPLICATE_THRESHOLD
                    ]
                    hint = f" (close to: {', '.join(close)})" if close else ""
                    errors.append(f"{eid}: unknown trait '{raw}'{hint}")
                continue

            usage[tid].append(eid)
            canonical = traits[tid]["label"]
            if raw != canonical:
                fixes.append((eid, i, raw, canonical))

    # Near-duplicate canonical traits, compared only within a facet.
    by_facet = {}
    for t in traits.values():
        by_facet.setdefault(t["facet"], []).append(t)
    for facet, group in by_facet.items():
        for a, b in combinations(group, 2):
            # Pairs already adjudicated as genuinely different stay quiet, so the
            # linter keeps its signal instead of crying wolf every run.
            if b["id"] in a.get("distinct_from", []) or a["id"] in b.get("distinct_from", []):
                continue
            score = jaccard(normalize(a["label"]), normalize(b["label"]))
            if score >= NEAR_DUPLICATE_THRESHOLD:
                warns.append(
                    f"[{facet}] '{a['label']}' ~ '{b['label']}' ({score:.0%} overlap) — "
                    f"merge, or add \"distinct_from\": [\"{b['id']}\"] to '{a['id']}'"
                )

    for tid, t in traits.items():
        count = len(set(usage[tid]))
        if t["status"] == "pending" and count >= 2:
            warns.append(f"'{t['label']}' is pending but used on {count} entries — promote it")
        elif t["status"] == "canonical" and count == 1:
            infos.append(f"'{t['label']}' used once ({usage[tid][0]}) — merge, or move to meta.notes")
        elif t["status"] == "canonical" and count == 0:
            infos.append(f"'{t['label']}' unused — fine if seeded, prune if stale")

    if fix and fixes:
        for eid, i, raw, canonical in fixes:
            entry = next(e for e in lib["entries"] if e["id"] == eid)
            entry["traits"][i] = canonical
        # Two different aliases can collapse onto the same canonical trait.
        for entry in lib["entries"]:
            seen, deduped = set(), []
            for t in entry.get("traits", []):
                if t not in seen:
                    seen.add(t)
                    deduped.append(t)
            if len(deduped) != len(entry.get("traits", [])):
                collapsed = len(entry["traits"]) - len(deduped)
                print(f"DEDUP {entry['id']}: collapsed {collapsed} duplicate trait(s)")
            entry["traits"] = deduped
        LIBRARY.write_text(json.dumps(lib, indent=2, ensure_ascii=False) + "\n")

    for label, items in (("ERROR", errors), ("WARN", warns), ("INFO", infos)):
        for m in items:
            print(f"{label:5} {m}")
    for eid, _, raw, canonical in fixes:
        verb = "fixed" if fix else "alias"
        print(f"{verb.upper():5} {eid}: '{raw}' -> '{canonical}'")

    total_traits = sum(len(set(u)) for u in usage.values())
    print(
        f"\n{len(lib['entries'])} entries, {len(traits)} traits in vocabulary, "
        f"{total_traits} trait uses"
    )
    if fixes and not fix:
        print(f"{len(fixes)} alias(es) resolvable — rerun with --fix to rewrite")
    if errors:
        print(f"{len(errors)} error(s)")
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
