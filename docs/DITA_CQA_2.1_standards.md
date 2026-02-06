# DITA Migration Standards (CQA 2.1)

This document summarizes the **Content Quality Assessment (CQA) 2.1** requirements for migrating MTA documentation to DITA/AEM. Use it together with the JTBD mapping and the `cqa_jtbd_validate.py` script.

Reference: *CQA 2.1 — Content Quality Assessment* (Pre-migration and Quality tabs).

---

## Pre-migration requirements (all required)

### Vale and AsciiDoc

- **Vale asciidoctor-dita-vale**: Content must pass the Vale `asciidoctor-dita-vale` check with no errors or warnings. Fix content type and markup issues before running the tool.
- **No text between include statements**: Assemblies (DITA maps) must contain only:
  - An introductory section (one or more paragraphs), and
  - Include statements.
  - You can have an "Additional resources" section at the end, after all includes.
- No prose or other content between two `include::` lines.

### Modularization

- **Content is modularized**: Content is split into modules (topics), not one long document.
- **Official templates**: Modules use:
  - **Concept** — explains what/why (e.g. `con_*.adoc`)
  - **Procedure** — step-by-step tasks (e.g. `proc_*.adoc`)
  - **Reference** — options, reference data (e.g. `ref_*.adoc`)
- **Required modular elements**: All required elements per the modular documentation templates checklist are present.
- **Assemblies**: Use the official assembly template. **One assembly = one user story** (aligns with JTBD).
- **TOC depth**: Content should not be deeply nested (recommended: no more than 3 levels).

### Titles and short descriptions

- **Short description on every module and assembly**:
  - Describes **why the user should read** the content (user benefit, not "This document describes...").
  - Concise; used as link preview and for search/SEO.
  - Includes keywords users are likely to search for.
  - **No self-referential language** ("This document describes...", "This section explains...").
- **AsciiDoc short descriptions**:
  - **Single paragraph**, **50–300 characters**.
  - Introduced with `[role="_abstract"]`.
  - **Blank line** between the level-0 title (`= Title`) and the short description in AsciiDoc.
- **Titles**: Brief, complete, and descriptive (see procedure module and peer review style guidelines).

### Procedures

- **Prerequisites**: If a procedure has prerequisites:
  - Use the "Prerequisites" label.
  - Use consistent formatting.
  - Do not exceed 10 prerequisites.
  - Do not include steps in prerequisites.

### Editorial

- Grammatically correct; American English.
- Information conveyed using the correct content type (concept vs procedure vs reference).

### URLs and links

- No broken links.

### Legal and branding

- Official product names used.
- Appropriate, legal-approved disclaimers for Technology Preview and Developer Preview (e.g. snippets in assemblies).

---

## Quality tab (important; address in AEM)

- **Scannable**: Short sentences (~22 words or fewer), short paragraphs (2–3 sentences), bulleted lists, graphics for complex procedures.
- **User-focused**: Content applies to target persona; addresses pain points; new terms/acronyms defined; Additional resources useful; admonitions used sparingly.
- **Assembly introduction**: Takes into account target audience/persona or skill level.
- **Procedures**: ≤10 steps; command examples; optional/conditional steps correctly formatted; verification steps when useful; Additional resources where relevant.
- **Links**: Links to non–Red Hat sites backed by Support or have appropriate disclaimers.
- **Style**: Minimum style guide; no excessive screen images; appropriate conversational tone; tables have captions and are explained; images have captions and alt text; conscious language.

---

## JTBD alignment

- **One user story per assembly**: Each assembly should map to one job story (e.g. "When I use the CLI, I want to analyze my applications so I can assess migration effort").
- **Short descriptions**: Written from a job perspective: why the user should read (outcome), not feature description.
- **Mapping**: See `docs/jtbd-mapping.yaml` for the MTA job → assembly/topic mapping.

---

## Checklist for authors

1. Run AsciiDoc Content Type Editor and fix errors before Vale.
2. Run Vale `asciidoctor-dita-vale` and fix all errors and warnings.
3. Ensure assemblies have only intro + includes (no text between includes).
4. Ensure every module and assembly has a short description: 50–300 chars, `[role="_abstract"]`, blank line after title.
5. Ensure titles are brief and descriptive; no self-referential short descriptions.
6. Procedures: prerequisites labeled; ≤10 steps; no steps inside prerequisites.
7. Use the JTBD mapping to confirm each assembly represents one user job.
