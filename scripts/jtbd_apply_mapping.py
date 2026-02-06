#!/usr/bin/env python3
"""
Apply JTBD (Jobs-to-be-Done) mapping to MTA documentation.

Reads docs/jtbd-mapping.yaml and updates assemblies (and optionally topics) to:
- Add JTBD job metadata (comment block with job id, statement, persona)
- Set or update short descriptions to be job-outcome focused (using shortdesc_focus
  from the mapping or deriving from job statement/outcomes)
- Keep short descriptions within CQA 2.1 length (50-300 chars)

Usage:
  python scripts/jtbd_apply_mapping.py [--dry-run] [--report] [--topics]
  python scripts/jtbd_apply_mapping.py --report   # Only list job -> assembly/topic mapping

Requires: PyYAML (pip install pyyaml)
Mapping: docs/jtbd-mapping.yaml
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

try:
    import yaml
except ImportError:
    yaml = None

SHORTDESC_MIN = 50
SHORTDESC_MAX = 300
RE_ROLE_ABSTRACT = re.compile(r"^\[role=\"_abstract\"\]\s*$", re.MULTILINE)
# Capture only the first paragraph after [role="_abstract"] (stop at double newline)
RE_FIRST_PARAGRAPH = re.compile(
    r"\[role=\"_abstract\"\]\s*\n(.*?)\n\s*\n",
    re.MULTILINE | re.DOTALL,
)
JTBD_BLOCK_START = "// JTBD job:"
JTBD_BLOCK_RE = re.compile(
    r"^// JTBD job:.*?(?=^// JTBD job:|\n(?:ifdef::|ifndef::|\[id=)|$)",
    re.MULTILINE | re.DOTALL,
)


def load_mapping(repo: Path) -> dict | None:
    path = repo / "docs" / "jtbd-mapping.yaml"
    if not path.is_file() or not yaml:
        return None
    with open(path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)


def build_path_to_job(mapping: dict, repo: Path) -> tuple[dict, dict]:
    """Return (assembly_path -> job_entry, topic_path -> job_entry). job_entry = (job, item)."""
    assembly_to_job = {}
    topic_to_job = {}
    for job in mapping.get("jobs", []):
        job_id = job.get("id", "")
        for a in job.get("assemblies", []):
            path = a.get("path") if isinstance(a, dict) else a
            if path:
                key = (repo / path).resolve()
                assembly_to_job[key] = (job, a if isinstance(a, dict) else {})
        for t in job.get("topics", []):
            key = (repo / t).resolve()
            topic_to_job[key] = (job, {})
    return assembly_to_job, topic_to_job


def job_shortdesc(job: dict, assembly_entry: dict, existing: str | None) -> str | None:
    """
    Build a CQA-compliant shortdesc (50-300 chars) from job or assembly shortdesc_focus.
    Returns None to keep existing shortdesc when we have no good replacement.
    """
    focus = assembly_entry.get("shortdesc_focus", "").strip()
    if focus:
        if len(focus) > SHORTDESC_MAX:
            focus = focus[: SHORTDESC_MAX - 1].rsplit(maxsplit=1)[0] + "."
        if len(focus) >= SHORTDESC_MIN:
            return focus
    # Derive from outcomes
    outcomes = job.get("outcomes", [])
    if outcomes:
        combined = " ".join(outcomes[:2])
        if len(combined) > SHORTDESC_MAX:
            combined = combined[: SHORTDESC_MAX - 1].rsplit(maxsplit=1)[0] + "."
        if len(combined) >= SHORTDESC_MIN:
            return combined
    # Derive from "so I can" part of statement
    statement = job.get("statement", "")
    if " so I can " in statement:
        part = statement.split(" so I can ", 1)[1].strip().rstrip(".")
        part = "So you can " + part
        if len(part) > SHORTDESC_MAX:
            part = part[: SHORTDESC_MAX - 1].rsplit(maxsplit=1)[0] + "."
        if len(part) >= SHORTDESC_MIN:
            return part
    # Keep existing if we have no good replacement
    return None


def first_paragraph_after_abstract(content: str) -> tuple[str, int, int]:
    """Return (first_paragraph_text, start_pos, end_pos)."""
    m = RE_FIRST_PARAGRAPH.search(content)
    if not m:
        return None, -1, -1
    para = m.group(1).replace("\n", " ").strip()
    return para, m.start(1), m.end(1)


def ensure_jtbd_comment_block(content: str, job: dict) -> str:
    """Ensure a JTBD comment block exists after :_mod-docs-content-type: (or at top)."""
    if JTBD_BLOCK_START in content and f"// JTBD job: {job.get('id', '')}" in content:
        return content
    block = (
        f"// JTBD job: {job.get('id', '')}\n"
        f"// Statement: {job.get('statement', '')}\n"
        f"// Persona: {job.get('persona', '')}\n"
    )
    # Insert after first line that looks like :_mod-docs-content-type: or :_content-type:
    match = re.search(r"^:_(?:mod-docs-)?content-type:.*$", content, re.MULTILINE)
    if match:
        insert_pos = match.end()
        return content[:insert_pos] + "\n" + block + content[insert_pos:]
    return block + "\n" + content


def update_assembly(path: Path, job: dict, assembly_entry: dict, dry_run: bool) -> bool:
    """Update one assembly with JTBD metadata and job-focused shortdesc. Return True if changed."""
    try:
        content = path.read_text(encoding="utf-8")
    except Exception:
        return False

    para, start, end = first_paragraph_after_abstract(content)
    new_shortdesc = job_shortdesc(job, assembly_entry, para)
    if new_shortdesc and len(new_shortdesc) > SHORTDESC_MAX:
        new_shortdesc = new_shortdesc[: SHORTDESC_MAX - 1].rsplit(maxsplit=1)[0] + "."
    if new_shortdesc and len(new_shortdesc) < SHORTDESC_MIN:
        new_shortdesc = (new_shortdesc + " See the section for steps and options.")[:SHORTDESC_MAX]

    modified = False
    # 1) Ensure JTBD comment block
    new_content = ensure_jtbd_comment_block(content, job)
    if new_content != content:
        content = new_content
        modified = True

    # 2) Replace first paragraph after [role="_abstract"] with job shortdesc when we have one
    if new_shortdesc and start >= 0 and para != new_shortdesc:
        content = content[:start] + new_shortdesc + content[end:]
        modified = True

    if modified and not dry_run:
        path.write_text(content, encoding="utf-8")
    return modified


def add_topic_jtbd_comment(path: Path, job: dict, dry_run: bool) -> bool:
    """Append a single-line JTBD comment at the end of the topic (before last newline). Return True if changed."""
    try:
        content = path.read_text(encoding="utf-8")
    except Exception:
        return False
    comment = f"\n// JTBD job: {job.get('id', '')}\n"
    if comment.strip() in content:
        return False
    content = content.rstrip("\n") + comment
    if not dry_run:
        path.write_text(content, encoding="utf-8")
    return True


def main() -> int:
    parser = argparse.ArgumentParser(description="Apply JTBD mapping to MTA documentation.")
    parser.add_argument("--docs-dir", type=Path, default=Path(__file__).resolve().parent.parent, help="Repository root")
    parser.add_argument("--dry-run", action="store_true", help="Do not write files")
    parser.add_argument("--report", action="store_true", help="Only print job -> path mapping and exit")
    parser.add_argument("--topics", action="store_true", help="Also add JTBD job comment to topics")
    parser.add_argument("--mapping", type=Path, default=None, help="Path to jtbd-mapping.yaml")
    args = parser.parse_args()
    repo = args.docs_dir
    mapping_path = args.mapping or (repo / "docs" / "jtbd-mapping.yaml")

    if not yaml:
        print("PyYAML is required: pip install pyyaml", file=sys.stderr)
        return 1
    if not mapping_path.is_file():
        print(f"Mapping not found: {mapping_path}", file=sys.stderr)
        return 1

    with open(mapping_path, "r", encoding="utf-8") as f:
        mapping = yaml.safe_load(f)
    if not mapping or "jobs" not in mapping:
        print("Invalid or empty mapping.", file=sys.stderr)
        return 1

    assembly_to_job, topic_to_job = build_path_to_job(mapping, repo)

    if args.report:
        for job in mapping.get("jobs", []):
            jid = job.get("id", "")
            print(f"\nJob: {jid}")
            print(f"  Statement: {job.get('statement', '')[:80]}...")
            for a in job.get("assemblies", []):
                p = a.get("path") if isinstance(a, dict) else a
                if p:
                    print(f"  Assembly: {p}")
            for t in job.get("topics", []):
                print(f"  Topic: {t}")
        return 0

    updated_assemblies = 0
    for path, (job, assembly_entry) in assembly_to_job.items():
        if not path.is_file():
            print(f"Skip (missing): {path.relative_to(repo)}", file=sys.stderr)
            continue
        if update_assembly(path, job, assembly_entry, args.dry_run):
            updated_assemblies += 1
            rel = path.relative_to(repo)
            print(f"{'[dry-run] ' if args.dry_run else ''}Updated assembly: {rel} (job: {job.get('id', '')})")

    updated_topics = 0
    if args.topics:
        for path, (job, _) in topic_to_job.items():
            if not path.is_file():
                continue
            if add_topic_jtbd_comment(path, job, args.dry_run):
                updated_topics += 1
                rel = path.relative_to(repo)
                print(f"{'[dry-run] ' if args.dry_run else ''}Updated topic: {rel} (job: {job.get('id', '')})")

    print(f"\nDone. Assemblies updated: {updated_assemblies}; Topics updated: {updated_topics}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
