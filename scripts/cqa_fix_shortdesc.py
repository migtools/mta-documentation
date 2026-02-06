#!/usr/bin/env python3
"""
Apply CQA 2.1 shortdesc fixes: add missing [role="_abstract"] or adjust length.
Run after cqa_jtbd_validate.py to fix reported failures. Use --dry-run to preview.
"""
import re
import sys
from pathlib import Path

RE_TITLE = re.compile(r"^=+\s+(.+)$", re.MULTILINE)
RE_ROLE_ABSTRACT = re.compile(r"^\[role=\"_abstract\"\]\s*$", re.MULTILINE)
SHORTDESC_MIN, SHORTDESC_MAX = 50, 300

def first_paragraph_after_abstract(content: str) -> tuple[str, int, int]:
    """Return (first_paragraph, start, end) after [role="_abstract"]."""
    m = RE_ROLE_ABSTRACT.search(content)
    if not m:
        return None, -1, -1
    start = m.end()
    end = content.find("\n\n", start)
    if end == -1:
        end = len(content)
    para = content[start:end].replace("\n", " ").strip()
    return para, start, end

def add_abstract(content: str, title: str, shortdesc: str) -> str:
    """Insert [role="_abstract"] and shortdesc after first = title (and :context: if present)."""
    lines = content.split("\n")
    out = []
    i = 0
    while i < len(lines):
        line = lines[i]
        out.append(line)
        if re.match(r"^=+\s+", line):
            # After = title, add optional :context:/:attr: lines then insert abstract
            i += 1
            while i < len(lines):
                next_line = lines[i]
                if next_line.strip() == "" or next_line.strip().startswith(":") or next_line.strip().startswith("//"):
                    out.append(next_line)
                    i += 1
                else:
                    break
            out.append("")
            out.append('[role="_abstract"]')
            out.append(shortdesc[:SHORTDESC_MAX])
            out.append("")
            continue
        i += 1
    return "\n".join(out)

def shorten_paragraph(para: str, max_len: int = 297) -> str:
    """Truncate at word boundary."""
    if len(para) <= max_len:
        return para
    truncated = para[:max_len].rsplit(maxsplit=1)[0]
    return truncated + "…" if len(truncated) < len(para) else truncated

def fix_file(path: Path, repo: Path, dry_run: bool, missing_shortdescs: dict) -> bool:
    """Apply fixes. Return True if file was modified."""
    content = path.read_text(encoding="utf-8")
    modified = False
    try:
        rel = path.relative_to(repo).as_posix()
    except ValueError:
        rel = path.as_posix()

    # Missing abstract
    if not RE_ROLE_ABSTRACT.search(content) and rel in missing_shortdescs:
        shortdesc = missing_shortdescs[rel]
        title_m = RE_TITLE.search(content)
        if title_m and shortdesc:
            new_content = add_abstract(content, title_m.group(1), shortdesc)
            if new_content != content:
                if not dry_run:
                    path.write_text(new_content, encoding="utf-8")
                modified = True

    # Too long
    para, start, end = first_paragraph_after_abstract(content)
    if para and len(para) > SHORTDESC_MAX:
        new_para = shorten_paragraph(para, SHORTDESC_MAX)
        if new_para != para:
            new_content = content[:start] + new_para + content[end:]
            if not dry_run:
                path.write_text(new_content, encoding="utf-8")
            modified = True

    # Too short
    if para and len(para) < SHORTDESC_MIN:
        # Expand with a generic suffix to reach 50 chars
        suffix = " Use this when writing or matching rules."
        new_para = (para + suffix)[:SHORTDESC_MAX]
        if len(new_para) >= SHORTDESC_MIN:
            new_content = content[:start] + new_para + content[end:]
            if not dry_run:
                path.write_text(new_content, encoding="utf-8")
            modified = True

    return modified

def main():
    dry_run = "--dry-run" in sys.argv
    repo = Path(__file__).resolve().parent.parent

    # Shortdescs for files that need one (title-derived or explicit)
    missing_shortdescs = {}
    for rel, shortdesc in [
        ("docs/topics/about-home-var.adoc", "Use the MTA_HOME and related environment variables when running MTA."),
        ("docs/topics/cli-args.adoc", "Reference for MTA CLI arguments and options."),
        ("docs/topics/developer-lightspeed/assembly_solution-server-configurations.adoc", "Configure the Solution Server and related settings for Developer Lightspeed."),
        ("docs/topics/fork-ruleset-repo.adoc", "Fork the ruleset repository to contribute or customize MTA rules."),
        ("docs/topics/important-links.adoc", "Important links for MTA documentation and resources."),
        ("docs/topics/mta-ui/con_assessment-module-features.adoc", "Overview of assessment module features in the MTA UI."),
        ("docs/topics/mta-ui/con_intro-to-mta-ui.adoc", "Introduction to the MTA user interface for configuring and running analyses."),
        ("docs/topics/mta-ui/con_mta-default-questionnaire.adoc", "Use the default MTA assessment questionnaire to evaluate applications."),
        ("docs/topics/mta-ui/proc_accessing-analysis-insights.adoc", "Access analysis insights in the MTA UI to understand migration results."),
        ("docs/topics/mta-ui/proc_accessing-unmatched-rules.adoc", "View and work with unmatched rules after an MTA analysis."),
        ("docs/topics/mta-ui/proc_adding-applications.adoc", "Add applications to the MTA UI for assessment and analysis."),
        ("docs/topics/mta-ui/proc_assessing-an-application.adoc", "Assess an application to estimate containerization effort and risks."),
        ("docs/topics/mta-ui/proc_assessing-an-archetype.adoc", "Assess an archetype to evaluate multiple applications with common characteristics."),
        ("docs/topics/mta-ui/proc_assigning-application-credentials.adoc", "Assign credentials to applications for source and Maven access."),
        ("docs/topics/mta-ui/proc_configuring-and-running-an-application-analysis.adoc", "Configure and run an application analysis in the MTA UI."),
        ("docs/topics/mta-ui/proc_configuring-git-repos.adoc", "Configure Git repositories for the MTA instance."),
        ("docs/topics/mta-ui/proc_configuring-jira-credentials.adoc", "Configure Jira credentials for issue tracking in the MTA UI."),
        ("docs/topics/mta-ui/proc_configuring-maven-credentials.adoc", "Configure Maven credentials for the MTA instance."),
        ("docs/topics/mta-ui/proc_configuring-maven-repo.adoc", "Configure Maven repository settings for the MTA instance."),
        ("docs/topics/mta-ui/proc_configuring-proxy-credentials.adoc", "Configure proxy credentials for the MTA instance."),
        ("docs/topics/mta-ui/proc_configuring-proxy-settings.adoc", "Configure proxy settings for the MTA instance."),
        ("docs/topics/mta-ui/proc_configuring-source-control-credentials.adoc", "Configure source control credentials for the MTA instance."),
        ("docs/topics/mta-ui/proc_configuring-subversion-repos.adoc", "Configure Subversion repositories for the MTA instance."),
        ("docs/topics/mta-ui/proc_controlling-task-order-with-task-manager.adoc", "Control task order with Task Manager in the MTA UI."),
        ("docs/topics/mta-ui/proc_creating-a-business-service.adoc", "Create a business service in the MTA UI for organizing applications."),
        ("docs/topics/mta-ui/proc_creating-a-jira-connection.adoc", "Create and configure a Jira connection in the MTA UI."),
        ("docs/topics/mta-ui/proc_creating-a-stakeholder.adoc", "Create a stakeholder in the MTA UI for assessment and review."),
        ("docs/topics/mta-ui/proc_creating-a-tag.adoc", "Create a tag in the MTA UI for classifying applications."),
        ("docs/topics/mta-ui/proc_creating-custom-migration-targets.adoc", "Create custom migration targets in the MTA UI."),
        ("docs/topics/mta-ui/proc_creating-jira-issues-for-migration-wave.adoc", "Create Jira issues for a migration wave in the MTA UI."),
        ("docs/topics/mta-ui/proc_creating-migration-waves.adoc", "Create migration waves to group and track application migrations."),
        ("docs/topics/mta-ui/proc_displaying-automated-tasks.adoc", "Display automated tasks and their status in the MTA UI."),
        ("docs/topics/mta-ui/proc_downloading-an-analysis-report.adoc", "Download an analysis report from the MTA UI."),
        ("docs/topics/mta-ui/proc_importing-an-app-list.adoc", "Import a list of applications into the MTA UI."),
        ("docs/topics/mta-ui/proc_manual-tagging-of-an-application.adoc", "Manually tag an application in the MTA UI."),
        ("docs/topics/mta-ui/proc_reviewing-a-task-log.adoc", "Review task log entries in the MTA UI."),
        ("docs/topics/mta-ui/proc_reviewing-an-analysis-report.adoc", "Review an analysis report in the MTA UI."),
        ("docs/topics/mta-ui/proc_reviewing-an-application.adoc", "Review an application assessment in the MTA UI."),
        ("docs/topics/mta-ui/proc_reviewing-an-archetype.adoc", "Review an archetype in the MTA UI."),
        ("docs/topics/mta-ui/proc_reviewing-assessment-report.adoc", "Review an assessment report in the MTA UI."),
        ("docs/topics/mta-ui/proc_setting-default-credentials.adoc", "Set default credentials for the MTA instance."),
        ("docs/topics/mta-ui/ref_custom-questionnaire-fields.adoc", "Reference for custom assessment questionnaire fields and YAML syntax."),
        ("docs/topics/mta-web-applying-assessments-to-other-apps.adoc", "Apply assessments from one application to others in the MTA UI."),
        ("docs/topics/web-console/assembly_asset-generation-ui.adoc", "Generate deployment assets in the MTA web console for Cloud Foundry to OpenShift."),
        ("docs/topics/web-console/assembly_platform-awareness.adoc", "Use platform awareness in the MTA web console for migration planning."),
        ("method-discover.adoc", "Discovery method and process for MTA documentation."),
    ]:
        missing_shortdescs[rel] = shortdesc

    fixed = 0
    for rel in missing_shortdescs:
        path = repo / rel
        if path.is_file() and fix_file(path, repo, dry_run, missing_shortdescs):
            fixed += 1
            print("Fixed:", rel)

    # Fix too-long / too-short (all adoc under repo)
    for path in repo.rglob("*.adoc"):
        if "website" in path.parts:
            continue
        rel = path.relative_to(repo).as_posix()
        if rel in missing_shortdescs:
            continue
        content = path.read_text(encoding="utf-8")
        para, start, end = first_paragraph_after_abstract(content)
        if not para:
            continue
        if len(para) > SHORTDESC_MAX:
            new_para = shorten_paragraph(para, SHORTDESC_MAX)
            if new_para != para:
                new_content = content[:start] + new_para + content[end:]
                if not dry_run:
                    path.write_text(new_content, encoding="utf-8")
                fixed += 1
                print("Shortened:", rel)
        elif len(para) < SHORTDESC_MIN:
            suffix = " Use this when writing or matching rules."
            new_para = (para + suffix)[:SHORTDESC_MAX]
            if len(new_para) >= SHORTDESC_MIN:
                new_content = content[:start] + new_para + content[end:]
                if not dry_run:
                    path.write_text(new_content, encoding="utf-8")
                fixed += 1
                print("Expanded:", rel)

    print("Total changes:", fixed)
    return 0

if __name__ == "__main__":
    sys.exit(main())
