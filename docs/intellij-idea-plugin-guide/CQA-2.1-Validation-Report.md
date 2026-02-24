# CQA 2.1 Validation Report — IntelliJ IDEA Plugin Guide

**Content location:** `docs/intellij-idea-plugin-guide` (book) and included topics/assemblies  
**Date of review:** 2025-02-24  
**Reference:** CQA 2.1 — Content Quality Assessment (Pre-migration and Quality tabs)  
**Vale configuration:** Red Hat and DITA (AsciiDoc) styles only; other packages (e.g. write-good) ignored per request.

---

## 1. Executive summary

| CQA 2.1 area | Status | Notes |
|--------------|--------|--------|
| **Vale (Red Hat + DITA)** | Does not meet | 10 errors, 455 warnings (465 total). Pre-migration requires zero errors and zero warnings. |
| **No text between includes** | Meets | Assemblies contain only intro and include statements. |
| **Short descriptions / modularization / procedures / editorial / URLs / legal** | Manual review | Not fully automated in this run. |

The IntelliJ IDEA Plugin Guide book **does not** currently meet the CQA 2.1 pre-migration requirement that content pass the Vale check with no errors or warnings. All 10 errors and a subset of high-priority warnings should be addressed before migration.

---

## 2. Vale validation (Red Hat and DITA only)

### 2.1 Configuration used

- **Config file:** `vale-cqa-redhat-dita.ini` (repo root)  
  - `Packages = RedHat`  
  - `BasedOnStyles = RedHat, AsciiDoc` for `*.adoc`  
  - Other packages (e.g. write-good) are **not** applied.
- **Styles:** Red Hat (`.github/styles/RedHat`) and AsciiDoc / DITA-style (`.github/styles/AsciiDoc`), e.g. image alt text.
- **Scope:** All `.adoc` under:
  - `docs/intellij-idea-plugin-guide/`
  - `docs/topics/templates/document-attributes.adoc`
  - `docs/topics/making-open-source-more-inclusive.adoc`
  - `docs/topics/mta-intellij-plugin/`
  - `assemblies/intellij-plugin-guide/`

Note: `assemblies/intellij-plugin-guide/` holds shared topics (e.g. developer-lightspeed, mta-cli, mta-ui, vscode); some findings apply to shared content used by multiple guides.

### 2.2 Results summary

| Severity | Count |
|----------|--------|
| **Errors** | 10 |
| **Warnings** | 455 |
| **Total** | 465 |

CQA 2.1 pre-migration: *"Content passes this Vale asciidoctor-dita-vale tool check with no errors or warnings"* — **Does not meet criteria.**

---

## 3. Errors (required fixes)

All 10 error-level findings must be fixed for pre-migration.

| # | File | Line | Rule | Message |
|---|------|------|------|---------|
| 1 | `assemblies/intellij-plugin-guide/topics/cli-args.adoc` | 68 | RedHat.TermsErrors | Use 'includes' rather than 'comes with'. |
| 2 | `assemblies/intellij-plugin-guide/topics/cli-args.adoc` | 81 | RedHat.Spacing | Keep one space between words in 'it.  In'. |
| 3 | `assemblies/intellij-plugin-guide/topics/mta-install/proc_installing-cli-for-docker.adoc` | 41 | RedHat.TermsErrors | Use 'installation program' rather than 'the installer'. |
| 4 | `assemblies/intellij-plugin-guide/topics/mta-ui/proc_configuring-jira-credentials.adoc` | 14 | RedHat.TermsErrors | Use 'Basic HTTP authentication' or 'Basic authentication' rather than 'Basic auth'. |
| 5 | `assemblies/intellij-plugin-guide/topics/mta-ui/proc_configuring-jira-credentials.adoc` | 26 | RedHat.TermsErrors | Use 'Basic HTTP authentication' or 'Basic authentication' rather than 'Basic Auth'. |
| 6 | `assemblies/intellij-plugin-guide/topics/mta-ui/proc_configuring-jira-credentials.adoc` | 28 | RedHat.TermsErrors | Use 'Basic HTTP authentication' or 'Basic authentication' rather than 'Basic Auth'. |
| 7 | `assemblies/intellij-plugin-guide/topics/mta-ui/proc_creating-a-jira-connection.adoc` | 30 | RedHat.TermsErrors | Use 'Basic HTTP authentication' or 'Basic authentication' rather than 'Basic Auth'. |
| 8 | `assemblies/intellij-plugin-guide/topics/mta-ui/proc_creating-a-jira-connection.adoc` | 32 | RedHat.TermsErrors | Use 'Basic HTTP authentication' or 'Basic authentication' rather than 'Basic Auth'. |
| 9 | `assemblies/intellij-plugin-guide/topics/mta-ui/proc_creating-jira-issues-for-migration-wave.adoc` | 29 | RedHat.TermsErrors | Use 'data center' rather than 'Datacenter'. |
| 10 | `assemblies/intellij-plugin-guide/topics/rules-development/yaml-builtin-provider.adoc` | 7 | RedHat.TermsErrors | Use 'built-in' rather than 'Builtin'. |

---

## 4. Warnings (sample by rule type)

455 warnings were reported. Below is a summary by **rule** and representative **files** (full list is in `vale-output.txt`).

### 4.1 Red Hat rules

| Rule | Typical message | Example files |
|------|------------------|---------------|
| **ConsciousLanguage** | Use 'blocklist'/'allowlist', avoid 'master'/'slave', 'blacklist'/'whitelist' | `making-open-source-more-inclusive.adoc`, `topics/making-open-source-more-inclusive.adoc` |
| **Spelling** | Word not in American English dictionary | Many (e.g. JDKs, cli, Quickfix, Ollama, LLMs, Lightspeed, containerless, Agentic, product/tech names in ref_mta-tech-tags.adoc) |
| **DoNotUseTerms** | Do not use color-only description; avoid "respective/respectively" | `proc_edit-code-file.adoc`, `proc_quick-fix.adoc`, developer-lightspeed, mta-ui ref_custom-questionnaire-fields.adoc |
| **Using** | Use 'by using' instead of 'using' after a noun | `about-ide-addons-intellij.adoc`, about-ide-addons.adoc, developer-lightspeed, release-notes |
| **HeadingPunctuation** | No end punctuation in headings | `what-is-the-toolkit.adoc` |
| **CaseSensitiveTerms** | Use 'JBoss EAP', 'Visual Studio Code', 'SSL/TLS', 'Podman Desktop', etc. | what-is-the-toolkit.adoc, developer-lightspeed, mta-cli, mta-ui, release-notes, vscode |
| **TermsWarnings** | Prefer 'you' vs 'I', 'is displayed' vs 'appears', 'might'/'can' vs 'may', 'such as' vs 'like', 'click' vs 'click on', 'required' vs 'desired', etc. | Multiple topics across assemblies |
| **Hyphens** | Use 'noninteractive', 're-create', 'plugin', 'open source', 'predefined' | cli-args.adoc, developer-lightspeed, mta-cli, release-notes, mta-install |
| **GitLinks** | Do not link to https://github.com unless approved | `document-attributes.adoc`, fork-ruleset-repo.adoc |
| **EmDash** | Do not use em dashes; use commas, parentheses, or colons | assembly_solution-server-configurations.adoc |
| **Slash** | Use 'or' or 'and' instead of slash in 'Server/Data', 'Start/Stop' | proc_creating-a-jira-connection.adoc, ref_known-issues-8-0.adoc |
| **SmartQuotes** | Use straight quotes rather than smart quotation marks | proc_creating-application-tags.adoc, proc_displaying-automated-tasks.adoc, proc_reviewing-an-archetype.adoc |

### 4.2 AsciiDoc / DITA-style rules

| Rule | Typical message | Example files |
|------|------------------|---------------|
| **AsciiDoc.ImageContainsAltText** | Image is missing accessibility alt tags | ref_example-code-suggestion.adoc, proc_adding-source-platform-application.adoc, proc_configuring-asset-repository.adoc, proc_generating-discovery-manifest-web.adoc |

---

## 5. CQA 2.1 Pre-migration checklist (relevant items)

| Requirement | Assessment | Notes |
|-------------|------------|--------|
| **Vale asciidoctor-dita-vale check (no errors or warnings)** | **Does not meet** | 10 errors, 455 warnings. Run used Red Hat + AsciiDoc (DITA-style) only; write-good and remote AsciiDocDITA package were not used. |
| **Assemblies: only intro + include statements; no text between includes** | **Meets** | `master.adoc` and `assembly_resolving-issues.adoc` contain only title, optional short description/abstract, and include statements. No narrative text between includes. |
| **Short descriptions (50–300 chars, [role="_abstract"], no self-referential language)** | Manual review | Present where checked; length and wording need manual audit. |
| **Modularization (templates, one user story per assembly, TOC depth)** | Manual review | Not automated. |
| **Procedures (prerequisites, steps, etc.)** | Manual review | Not automated. |
| **Editorial (grammar, content type, links, legal/branding)** | Manual review | Vale supports style and conscious language; full editorial check is manual. |

---

## 6. CQA 2.1 Quality tab (overview)

The Quality tab (readability, user focus, procedures, editorial, links, etc.) is assessed manually by reviewers. Vale output supports:

- **Content follows minimum style guide requirements** (Red Hat + AsciiDoc rules).
- **Conscious language guidelines** (ConsciousLanguage and related rules).

Other quality measures (e.g. scannability, clarity, persona, procedures, links) are not automated in this validation.

---

## 7. Assembly structure verification (no text between includes)

### 7.1 `docs/intellij-idea-plugin-guide/master.adoc`

- Contains: attributes, level-0 title, optional comments, and **include statements** only.
- **No narrative paragraphs between include statements.**  
**Meets** CQA requirement.

### 7.2 `assemblies/intellij-plugin-guide/assembly_resolving-issues.adoc`

- Contains: attributes, title `= Resolving issues`, short description (`[role="_abstract"]` and bullet list), then two **include** statements.
- **No narrative text between the two includes.**  
**Meets** CQA requirement.

---

## 8. Files in scope (IntelliJ IDEA Plugin Guide book)

**Directly included from the book:**

- `docs/intellij-idea-plugin-guide/master.adoc`
- `docs/topics/templates/document-attributes.adoc`
- `docs/topics/making-open-source-more-inclusive.adoc`
- `docs/topics/mta-intellij-plugin/about-ide-addons-intellij.adoc`
- `docs/topics/mta-intellij-plugin/what-is-the-toolkit.adoc`
- `docs/topics/mta-intellij-plugin/installing-intellij-idea-plugin.adoc`
- `docs/topics/mta-intellij-plugin/intellij-idea-plugin-run-configuration.adoc`
- `docs/topics/mta-intellij-plugin/intellij-idea-plugin-reviewing-issues.adoc`
- `docs/topics/mta-intellij-plugin/proc_quick-fix.adoc`
- `docs/topics/mta-intellij-plugin/proc_edit-code-file.adoc`
- `assemblies/intellij-plugin-guide/assembly_resolving-issues.adoc`

**Also validated:** All other `.adoc` under `assemblies/intellij-plugin-guide/` (shared topics).

---

## 9. How to re-run Vale (Red Hat + DITA only)

From the repository root:

```bash
vale --config=vale-cqa-redhat-dita.ini --no-exit --output=line \
  docs/intellij-idea-plugin-guide/master.adoc \
  docs/topics/templates/document-attributes.adoc \
  docs/topics/making-open-source-more-inclusive.adoc \
  docs/topics/mta-intellij-plugin/ \
  assemblies/intellij-plugin-guide/
```

Full line-oriented output from the run used for this report is in:

`docs/intellij-idea-plugin-guide/vale-output.txt`

---

## 10. Recommendations

1. **Fix all 10 errors** (TermsErrors and Spacing) so the book can meet the Vale pre-migration requirement.
2. **Triage warnings** by priority (e.g. ConsciousLanguage, CaseSensitiveTerms, HeadingPunctuation, image alt text).
3. Run the **AsciiDoc Content Type Editor** (CQA step 1) and fix content type issues before re-running Vale to reduce noise.
4. Use the **Vale VS Code extension** for ongoing linting while editing.
5. Complete remaining **Pre-migration** and **Quality** items via manual review and Jira per CQA 2.1.

---

*Report generated from CQA 2.1 (Content Quality Assessment) and Vale run with Red Hat and DITA (AsciiDoc) styles only. No documentation source files were modified.*
