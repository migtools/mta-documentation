# MTA Documentation Scripts

## CQA 2.1 + JTBD validation (`cqa_jtbd_validate.py`)

Validates AsciiDoc content against **DITA migration standards (CQA 2.1)** and reports alignment with the **JTBD (Jobs-to-be-Done)** mapping.

### Requirements

- Python 3.8+
- **PyYAML** (optional, for JTBD mapping): `pip install pyyaml`

### Usage

```bash
# From repository root
python scripts/cqa_jtbd_validate.py

# JTBD mapping coverage only (list files that are in the mapping)
python scripts/cqa_jtbd_validate.py --jtbd-only

# List files that need short description fixes
python scripts/cqa_jtbd_validate.py --fix-shortdesc

# Machine-readable JSON output
python scripts/cqa_jtbd_validate.py --json

# Custom paths
python scripts/cqa_jtbd_validate.py --docs-dir /path/to/repo --mapping docs/jtbd-mapping.yaml
```

### What it checks (CQA 2.1)

- **Short descriptions**: Present, 50–300 characters, `[role="_abstract"]`, no self-referential language, blank line between level-0 title and short description
- **Assemblies**: No content between `include::` statements (conditionals and attribute toggles at end of file are allowed)
- **Content types**: CONCEPT, PROCEDURE, REFERENCE, ASSEMBLY
- **Procedures**: Step count ≤ 10

### Related files

- **JTBD mapping**: `docs/jtbd-mapping.yaml` — maps jobs (user stories) to assemblies and topics
- **DITA/CQA standards**: `docs/DITA_CQA_2.1_standards.md` — summary of CQA 2.1 pre-migration and quality requirements

Reference: *CQA 2.1 — Content Quality Assessment* (Pre-migration and Quality tabs).

---

## Apply JTBD mapping (`jtbd_apply_mapping.py`)

Applies the **JTBD mapping** (`docs/jtbd-mapping.yaml`) to documentation: adds job metadata to assemblies and optionally updates short descriptions to be job-outcome focused.

### What it does

- **Assemblies**: Inserts a JTBD comment block (job id, statement, persona) after the content-type line, and sets or updates the first paragraph after `[role="_abstract"]` to a job-focused short description (using `shortdesc_focus` from the mapping or deriving from job outcomes/statement). Keeps short descriptions within 50–300 characters (CQA 2.1).
- **Topics** (optional): With `--topics`, appends a `// JTBD job: <id>` comment to each topic in the mapping for traceability.

### Usage

```bash
# From repository root
python scripts/jtbd_apply_mapping.py              # Update assemblies with JTBD metadata and shortdescs
python scripts/jtbd_apply_mapping.py --dry-run   # Show what would be updated, no file writes
python scripts/jtbd_apply_mapping.py --report    # Print job → assembly/topic mapping only
python scripts/jtbd_apply_mapping.py --topics   # Also add JTBD job comment to mapped topics
```

### Requirements

- Python 3.8+
- PyYAML: `pip install pyyaml`
- Mapping file: `docs/jtbd-mapping.yaml`
