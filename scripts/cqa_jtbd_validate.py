#!/usr/bin/env python3
"""
CQA 2.1 + JTBD validation script for MTA documentation.

Validates AsciiDoc content against DITA migration standards (CQA 2.1) and
checks alignment with the JTBD (Jobs-to-be-Done) mapping.

Usage:
  python scripts/cqa_jtbd_validate.py [--docs-dir DOCS] [--mapping PATH] [--jtbd-only]
  python scripts/cqa_jtbd_validate.py --fix-shortdesc   # Report only; no file writes by default

Requirements: PyYAML (pip install pyyaml)

Reference: CQA 2.1 — Content Quality Assessment (Pre-migration and Quality tabs).
           docs/DITA_CQA_2.1_standards.md
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path
from typing import Any

# Optional YAML
try:
    import yaml
except ImportError:
    yaml = None

# -----------------------------------------------------------------------------
# Constants (CQA 2.1)
# -----------------------------------------------------------------------------
SHORTDESC_MIN_CHARS = 50
SHORTDESC_MAX_CHARS = 300
ROLE_ABSTRACT = '[role="_abstract"]'
MAX_PROCEDURE_STEPS = 10
MAX_PREREQUISITES = 10

CONTENT_TYPES = {"CONCEPT", "PROCEDURE", "REFERENCE", "ASSEMBLY", "SNIPPET"}
MODULE_CONTENT_TYPES = {"CONCEPT", "PROCEDURE", "REFERENCE"}

# Patterns
RE_INCLUDE = re.compile(r"^include::([^\[]+)\[", re.MULTILINE)
RE_LEVEL0_TITLE = re.compile(r"^=+\s+.+$", re.MULTILINE)
RE_ROLE_ABSTRACT = re.compile(r"^\[role=\"_abstract\"\]", re.MULTILINE)
RE_CONTENT_TYPE = re.compile(
    r"^:_(?:mod-docs-)?content-type:\s*(.+)$", re.MULTILINE | re.IGNORECASE
)
RE_PREREQUISITES = re.compile(r"^\.Prerequisites?\s*$", re.MULTILINE | re.IGNORECASE)
RE_STEP = re.compile(r"^\.\s+\d+\.\s+", re.MULTILINE)
RE_SELF_REF = re.compile(
    r"\b(this\s+(?:document|section|module|topic|guide)\s+(?:describes|explains|contains)|"
    r"in\s+this\s+(?:document|section))\b",
    re.IGNORECASE,
)


def load_jtbd_mapping(mapping_path: Path) -> dict[str, Any] | None:
    """Load docs/jtbd-mapping.yaml if PyYAML is available."""
    if not yaml:
        return None
    if not mapping_path.is_file():
        return None
    with open(mapping_path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)


def collect_mapped_paths(jtbd: dict[str, Any], repo_root: Path) -> set[Path]:
    """Return set of repo-relative paths that appear in the JTBD mapping."""
    out: set[Path] = set()
    for job in jtbd.get("jobs", []):
        for a in job.get("assemblies", []):
            p = a.get("path") if isinstance(a, dict) else a
            if p:
                out.add(repo_root / p)
        for t in job.get("topics", []):
            out.add(repo_root / t)
    return out


def get_content_type(content: str) -> str | None:
    """Extract _content-type or _mod-docs-content-type from AsciiDoc."""
    m = RE_CONTENT_TYPE.search(content)
    return m.group(1).strip().upper() if m else None


def get_shortdesc_paragraph(content: str) -> tuple[str | None, int, int]:
    """
    Find the short description after [role="_abstract"] (CQA: one paragraph only).
    Returns (paragraph_text, start_offset, end_offset) or (None, -1, -1).
    """
    m = RE_ROLE_ABSTRACT.search(content)
    if not m:
        return None, -1, -1
    start = m.end()
    rest = content[start:]
    i = 0
    while i < len(rest) and rest[i : i + 1] in ("\n", "\r"):
        i += 1
    block_start = i
    # First paragraph only: stop at first blank line (CQA shortdesc = single paragraph)
    lines: list[str] = []
    while i < len(rest):
        line_end = rest.find("\n", i)
        if line_end == -1:
            line_end = len(rest)
        line = rest[i:line_end]
        if line.strip() == "":
            break
        lines.append(line)
        i = line_end + 1
    text = " ".join(l.strip() for l in lines if l.strip()).strip()
    return text or None, start + block_start, start + i


def check_blank_line_after_title(content: str) -> tuple[bool, str]:
    """CQA: blank line between level-0 title and short description."""
    title_m = RE_LEVEL0_TITLE.search(content)
    abstract_m = RE_ROLE_ABSTRACT.search(content)
    if not title_m or not abstract_m:
        return True, ""
    title_end = title_m.end()
    between = content[title_end : abstract_m.start()]
    if between.strip() and not re.search(r"^\s*\n\s*\n", between):
        return False, "Missing blank line between level-0 title and [role=\"_abstract\"]"
    return True, ""


def check_shortdesc_length(text: str) -> tuple[bool, str]:
    """CQA: short description 50-300 characters."""
    if not text:
        return False, "Short description is missing"
    n = len(text)
    if n < SHORTDESC_MIN_CHARS:
        return False, f"Short description too short ({n} < {SHORTDESC_MIN_CHARS} chars)"
    if n > SHORTDESC_MAX_CHARS:
        return False, f"Short description too long ({n} > {SHORTDESC_MAX_CHARS} chars)"
    return True, ""


def check_self_referential(text: str) -> tuple[bool, str]:
    """CQA: no self-referential language in short description."""
    if not text:
        return True, ""
    if RE_SELF_REF.search(text):
        return False, "Short description contains self-referential language"
    return True, ""


# Lines that are allowed between include statements (CQA: no *content* between includes)
_ALLOWED_BETWEEN_INCLUDES = (
    re.compile(r"^\s*//"),               # comments
    re.compile(r"^\s*ifdef::"),          # AsciiDoc conditionals
    re.compile(r"^\s*ifndef::"),
    re.compile(r"^\s*endif::"),
    re.compile(r"^\s*:\![a-z0-9_-]+:?\s*$"),  # attribute toggle :!context:
    re.compile(r"^\s*:[a-z0-9_-]+:.*$"),      # attribute set :context: value
    re.compile(r"^\s*={2,}\s+"),             # section heading (e.g. == Additional resources)
    re.compile(r"^\s*\[role=.*\]\s*$"),     # role attribute
    re.compile(r"^\s*\*\s+link:"),           # list item with link
)


def check_assembly_no_text_between_includes(content: str) -> tuple[bool, list[str]]:
    """
    CQA: assemblies must not have content between include statements.
    Conditionals (ifdef/ifndef/endif) and attribute toggles after includes are allowed.
    Returns (ok, list of issue descriptions).
    """
    issues: list[str] = []
    lines = content.splitlines()
    in_includes = False
    for i, line in enumerate(lines, 1):
        stripped = line.strip()
        if stripped.startswith("include::"):
            in_includes = True
            continue
        if in_includes and stripped and not stripped.startswith("//"):
            if "include::" in stripped:
                continue
            if any(pat.search(line) for pat in _ALLOWED_BETWEEN_INCLUDES):
                continue
            # Blank lines are allowed
            if not stripped:
                continue
            issues.append(f"Line {i}: Text between include statements: {stripped[:60]}...")
    return len(issues) == 0, issues


def count_procedure_steps(content: str) -> int:
    """Count numbered steps in a procedure (e.g. . 1. Step one)."""
    return len(RE_STEP.findall(content))


def validate_module(
    path: Path, content: str, content_type: str | None
) -> list[tuple[str, str]]:
    """Run CQA checks on a topic/module. Returns list of (check_name, message)."""
    errors: list[tuple[str, str]] = []

    if content_type and content_type not in CONTENT_TYPES:
        errors.append(("content_type", f"Unknown content type: {content_type}"))

    # Short description
    has_abstract = RE_ROLE_ABSTRACT.search(content) is not None
    if content_type in MODULE_CONTENT_TYPES or content_type == "ASSEMBLY":
        if not has_abstract:
            errors.append(("shortdesc", "Missing [role=\"_abstract\"]"))
        else:
            ok, msg = check_blank_line_after_title(content)
            if not ok:
                errors.append(("shortdesc", msg))
            text, _, _ = get_shortdesc_paragraph(content)
            ok, msg = check_shortdesc_length(text or "")
            if not ok:
                errors.append(("shortdesc", msg))
            if text:
                ok, msg = check_self_referential(text)
                if not ok:
                    errors.append(("shortdesc", msg))

    if content_type == "PROCEDURE":
        step_count = count_procedure_steps(content)
        if step_count > MAX_PROCEDURE_STEPS:
            errors.append(
                ("procedure", f"Procedure has {step_count} steps (max {MAX_PROCEDURE_STEPS})")
            )
        if RE_PREREQUISITES.search(content):
            # Could add: count prerequisite items and warn if > 10
            pass

    return errors


def validate_assembly(path: Path, content: str) -> list[tuple[str, str]]:
    """Run CQA checks on an assembly. Returns list of (check_name, message)."""
    errors: list[tuple[str, str]] = []
    content_type = get_content_type(content)
    if content_type != "ASSEMBLY":
        errors.append(("content_type", f"Assembly should have _mod-docs-content-type: ASSEMBLY, got {content_type}"))

    ok, issues = check_assembly_no_text_between_includes(content)
    for msg in issues:
        errors.append(("no_text_between_includes", msg))

    # Reuse module shortdesc checks
    errors.extend(validate_module(path, content, "ASSEMBLY"))
    return errors


def scan_adoc_files(base: Path) -> list[Path]:
    """Return list of .adoc files under base."""
    return sorted(base.rglob("*.adoc"))


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Validate MTA docs against CQA 2.1 and JTBD mapping."
    )
    parser.add_argument(
        "--docs-dir",
        type=Path,
        default=Path(__file__).resolve().parent.parent,
        help="Repository root (contains docs/, assemblies/)",
    )
    parser.add_argument(
        "--mapping",
        type=Path,
        default=None,
        help="Path to jtbd-mapping.yaml (default: docs/jtbd-mapping.yaml)",
    )
    parser.add_argument(
        "--jtbd-only",
        action="store_true",
        help="Only report JTBD mapping coverage (no CQA checks)",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Output machine-readable JSON (summary only)",
    )
    parser.add_argument(
        "--fix-shortdesc",
        action="store_true",
        help="List files that need shortdesc fixes (no file writes)",
    )
    args = parser.parse_args()
    repo = args.docs_dir
    mapping_path = args.mapping or (repo / "docs" / "jtbd-mapping.yaml")

    jtbd = load_jtbd_mapping(mapping_path)
    mapped_paths = collect_mapped_paths(jtbd, repo) if jtbd else set()

    # Paths: mapping uses paths relative to repo (e.g. assemblies/..., docs/topics/...)
    all_adoc = [p for p in scan_adoc_files(repo) if "website" not in p.parts]
    try:
        repo_resolved = repo.resolve()
    except Exception:
        repo_resolved = repo

    def rel_path(p: Path) -> Path:
        try:
            return p.resolve().relative_to(repo_resolved)
        except ValueError:
            return p

    failed: list[tuple[Path, list[tuple[str, str]]]] = []
    passed = 0

    for path in all_adoc:
        try:
            content = path.read_text(encoding="utf-8")
        except Exception as e:
            failed.append((path, [("read", str(e))]))
            continue

        rel = rel_path(path)
        content_type = get_content_type(content)
        if args.jtbd_only:
            path_resolved = path.resolve()
            mapped_resolved = {q.resolve() for q in mapped_paths}
            if path_resolved in mapped_resolved:
                print(f"MAPPED: {rel}")
            continue

        if "assembly" in path.name and "assembly_" in path.name:
            errs = validate_assembly(path, content)
        else:
            errs = validate_module(path, content, content_type)

        if errs:
            failed.append((path, errs))
        else:
            passed += 1

    if args.jtbd_only:
        if jtbd:
            print(f"\nJTBD jobs: {len(jtbd.get('jobs', []))}")
        return 0

    # Report
    if args.json:
        import json
        out = {
            "passed": passed,
            "failed_count": len(failed),
            "failed": [
                {"path": str(rel_path(p)), "errors": [{"check": c, "message": m} for c, m in e]}
                for p, e in failed
            ],
        }
        print(json.dumps(out, indent=2))
        return 0 if not failed else 1

    for path, errs in failed:
        print(f"{path}")
        for check, msg in errs:
            print(f"  - [{check}] {msg}")
    if failed:
        print(f"\nTotal: {passed} passed, {len(failed)} failed")
    else:
        print(f"All {passed} checked files passed CQA 2.1 checks.")

    if args.fix_shortdesc and failed:
        shortdesc_fails = [p for p, e in failed if any(c == "shortdesc" for c, _ in e)]
        if shortdesc_fails:
            print("\nFiles needing shortdesc fixes:")
            for p in shortdesc_fails:
                print(f"  {p}")

    return 0 if not failed else 1


if __name__ == "__main__":
    sys.exit(main())
