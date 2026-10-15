#!/usr/bin/env python3
"""Validate data/ai_services.csv and run tests/match_cases.csv against it.

Matching semantics (same as a Splunk WILDCARD lookup with max_matches=1, and what
most consumers should implement):
  * patterns are matched against the whole lowercased hostname, trailing dot removed
  * '*' matches any run of characters, including dots
  * rows are tried in file order and the FIRST match wins

Checks:
  * header, required fields, allowed categories and roles
  * counts_as_usage is 1 exactly for the app, api and agent roles
  * host_pattern syntax; no duplicates
  * no field contains a comma or double quote (keeps the file trivially parseable)
  * source is an https:// URL or blank
  * confidence is documented, evidence, hostname or low; documented needs a source
  * shadowing: no row can ever be reached because an earlier row matches everything it would
  * every case in tests/match_cases.csv classifies to the expected service and role

Exit status 0 when clean, 1 otherwise. Standard library only.
"""

import csv
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / "data" / "ai_services.csv"
CASES = ROOT / "tests" / "match_cases.csv"

HEADER = ["host_pattern", "service", "vendor", "category", "role", "counts_as_usage", "source", "confidence", "notes"]
CATEGORIES = {"Chat assistant", "Coding assistant", "AI platform", "AI browser", "Research", "Creative"}
ROLES = {"app", "api", "agent", "portal", "web", "auth", "cdn", "telemetry", "download", "other"}
USAGE_ROLES = {"app", "api", "agent"}
CONFIDENCE = {"documented", "evidence", "hostname", "low"}
PATTERN_RE = re.compile(r"^[a-z0-9*]([a-z0-9*.-]*[a-z0-9*])?$")
SOURCE_RE = re.compile(r"^(https://\S+)?$")


def to_regex(pattern: str) -> re.Pattern:
    return re.compile("^" + ".*".join(re.escape(part) for part in pattern.split("*")) + "$")


def classify(rows, hostname: str):
    host = hostname.lower().rstrip(".")
    for r in rows:
        if r["_rx"].match(host):
            return r
    return None


def probes(pattern: str) -> list[str]:
    """Concrete hostnames a pattern matches, used to detect shadowing."""
    return [pattern.replace("*", fill) for fill in ("zz9", "zz9.zz9")]


def main() -> int:
    errors: list[str] = []

    with DATA.open(newline="") as f:
        reader = csv.DictReader(f)
        if reader.fieldnames != HEADER:
            print(f"{DATA.name}: header must be {','.join(HEADER)}")
            return 1
        rows = list(reader)

    seen: dict[str, int] = {}
    for n, r in enumerate(rows, start=2):
        where = f"{DATA.name}:{n} ({r.get('host_pattern')})"
        if None in r:
            errors.append(f"{where}: too many columns (unquoted comma in a field?)")
        for k in HEADER:
            v = r.get(k)
            if v is None:
                errors.append(f"{where}: missing column {k}")
                continue
            if any(c in v for c in ',"'):
                errors.append(f"{where}: {k} contains a comma or double quote")
            if k not in ("notes", "source") and not v.strip():
                errors.append(f"{where}: {k} is empty")
        pat = r["host_pattern"]
        if pat != pat.lower() or not PATTERN_RE.match(pat) or ".." in pat:
            errors.append(f"{where}: invalid host_pattern")
        if pat in seen:
            errors.append(f"{where}: duplicate of line {seen[pat]}")
        seen.setdefault(pat, n)
        if r["category"] not in CATEGORIES:
            errors.append(f"{where}: category must be one of {sorted(CATEGORIES)}")
        if r["role"] not in ROLES:
            errors.append(f"{where}: role must be one of {sorted(ROLES)}")
        if r["counts_as_usage"] != ("1" if r["role"] in USAGE_ROLES else "0"):
            errors.append(f"{where}: counts_as_usage must be 1 for roles {sorted(USAGE_ROLES)} and 0 otherwise")
        if not SOURCE_RE.match(r["source"]):
            errors.append(f"{where}: source must be an https:// URL or blank")
        if r["confidence"] not in CONFIDENCE:
            errors.append(f"{where}: confidence must be one of {sorted(CONFIDENCE)}")
        elif r["confidence"] == "documented" and not r["source"]:
            errors.append(f"{where}: confidence documented needs a source URL")
        r["_rx"] = to_regex(pat)
        r["_line"] = n

    # Shadowing: a later row is unreachable if an earlier row matches all of its probes.
    for j, later in enumerate(rows):
        for earlier in rows[:j]:
            if all(earlier["_rx"].match(p) for p in probes(later["host_pattern"])):
                errors.append(f"{DATA.name}:{later['_line']} ({later['host_pattern']}) is shadowed by "
                              f"line {earlier['_line']} ({earlier['host_pattern']}); move it above that row")
                break

    with CASES.open(newline="") as f:
        cases = list(csv.DictReader(f))
    for n, c in enumerate(cases, start=2):
        hit = classify(rows, c["hostname"])
        got = (hit["service"], hit["role"]) if hit else ("", "")
        want = (c["expected_service"], c["expected_role"])
        if got != want:
            where = f" (line {hit['_line']}: {hit['host_pattern']})" if hit else ""
            errors.append(f"{CASES.name}:{n}: {c['hostname']} -> {got}{where}, expected {want}")

    for e in errors:
        print(e)
    print(f"{len(rows)} patterns, {len(cases)} test cases, {len(errors)} problem(s)")
    return 1 if errors else 0


if __name__ == "__main__":
    sys.exit(main())
