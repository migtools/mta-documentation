#!/usr/bin/env python3
"""
MTA Documentation Vale Issue Fixer

This script analyzes and fixes Vale linting issues in the MTA documentation
based on CQA 2.1 Content Quality Assessment guidelines.

Only RedHat.* and AsciiDocDITA.* checks are processed (write-good is ignored).

It handles the following issue types:

RedHat Style Checks (auto-fixable):
- RedHat.TermsErrors: Automatic replacements (e.g., "comes with" -> "includes")
- RedHat.TermsWarnings: Automatic replacements (e.g., "may" -> "might" or "can")
- RedHat.Hyphens: Automatic hyphenation fixes (e.g., "non-interactive" -> "noninteractive")
- RedHat.Using: "using" -> "by using" after nouns
- RedHat.Spacing: Fix double spaces
- RedHat.CaseSensitiveTerms: Fix case-sensitive terms (e.g., "OS" -> "operating system")
- RedHat.ConsciousLanguage: Replace problematic terminology

AsciiDocDITA Checks (manual review):
- AsciiDocDITA.ShortDescription: Add [role="_abstract"] where missing
- AsciiDocDITA.ContentType: Add :_mod-docs-content-type: where missing
- AsciiDocDITA.DocumentTitle: Add document title where missing
- AsciiDocDITA.TaskContents: Add .Procedure block title where missing

Usage:
    python fix_vale_issues.py [--dry-run] [--auto-fix] [--report-only] [path]

Options:
    --dry-run      Show what would be changed without making changes
    --auto-fix     Automatically fix issues with clear replacements
    --report-only  Only generate a report without making changes
    --refresh      Force re-run Vale instead of using cached output
    path           Path to scan (default: docs/)
"""

import argparse
import json
import os
import re
import subprocess
import sys
from collections import defaultdict
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional


@dataclass
class ValeIssue:
    """Represents a single Vale issue."""
    file: str
    line: int
    span: tuple
    check: str
    severity: str
    message: str
    match: str
    action_name: Optional[str] = None
    action_params: Optional[list] = None

    @property
    def can_auto_fix(self) -> bool:
        """Check if this issue can be automatically fixed."""
        # Issues with explicit replacement actions
        if self.action_name in ('replace', 'edit'):
            return True
        # Specific checks we know how to fix
        auto_fixable_checks = [
            'RedHat.TermsErrors',
            'RedHat.TermsWarnings',
            'RedHat.Hyphens',
            'RedHat.Using',
            'RedHat.Spacing',
            'RedHat.CaseSensitiveTerms',
        ]
        return self.check in auto_fixable_checks and self.action_params


@dataclass
class FixResult:
    """Result of attempting to fix an issue."""
    success: bool
    original: str
    replacement: str
    message: str


class ValeIssueFixer:
    """Fixes Vale issues in documentation files."""

    # Files that should be excluded from conscious language fixes
    # (they're discussing the terms, not using them problematically)
    CONSCIOUS_LANGUAGE_EXCLUSIONS = [
        'making-open-source-more-inclusive.adoc',
    ]

    def __init__(self, base_path: str = '.', dry_run: bool = False, refresh: bool = False):
        self.base_path = Path(base_path)
        self.dry_run = dry_run
        self.refresh = refresh
        self.issues_by_file: dict[str, list[ValeIssue]] = defaultdict(list)
        self.fix_results: list[tuple[ValeIssue, FixResult]] = []
        self.manual_review_issues: list[ValeIssue] = []

    def run_vale(self, path: str = 'docs/') -> dict:
        """Run Vale and return JSON output."""
        # Check if we have a cached vale output file
        cache_file = self.base_path / 'vale_output.json'
        if cache_file.exists() and not self.refresh:
            print(f"Using cached Vale output from {cache_file}")
            print("Use --refresh to re-run Vale")
            try:
                return json.loads(cache_file.read_text())
            except json.JSONDecodeError:
                print("Cache file is invalid, running Vale...")

        cmd = ['vale', '--output=JSON', path]
        print(f"Running: {' '.join(cmd)}")
        print("This may take a few minutes for large documentation sets...")
        try:
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                cwd=self.base_path,
                timeout=300  # 5 minute timeout
            )
            # Vale returns exit code 1 when issues are found
            if result.stdout:
                # Save to cache for faster re-runs
                cache_file.write_text(result.stdout)
                return json.loads(result.stdout)
            return {}
        except subprocess.TimeoutExpired:
            print("Error: Vale timed out after 5 minutes")
            return {}
        except subprocess.CalledProcessError as e:
            print(f"Error running Vale: {e}")
            return {}
        except json.JSONDecodeError as e:
            print(f"Error parsing Vale output: {e}")
            return {}

    # Only include these check prefixes (ignore write-good, etc.)
    INCLUDED_CHECK_PREFIXES = ['RedHat.', 'AsciiDocDITA.']

    def parse_issues(self, vale_output: dict) -> None:
        """Parse Vale JSON output into ValeIssue objects."""
        for file_path, issues in vale_output.items():
            for issue in issues:
                check = issue['Check']
                
                # Filter to only include RedHat.* and AsciiDocDITA.* checks
                if not any(check.startswith(prefix) for prefix in self.INCLUDED_CHECK_PREFIXES):
                    continue
                
                action = issue.get('Action', {})
                vale_issue = ValeIssue(
                    file=file_path,
                    line=issue['Line'],
                    span=tuple(issue['Span']),
                    check=check,
                    severity=issue['Severity'],
                    message=issue['Message'],
                    match=issue['Match'],
                    action_name=action.get('Name'),
                    action_params=action.get('Params'),
                )
                self.issues_by_file[file_path].append(vale_issue)

    def fix_issue(self, issue: ValeIssue, content: str) -> tuple[str, FixResult]:
        """Attempt to fix a single issue in the content."""
        # Skip conscious language issues in exclusion files
        if issue.check == 'RedHat.ConsciousLanguage':
            for excluded in self.CONSCIOUS_LANGUAGE_EXCLUSIONS:
                if excluded in issue.file:
                    return content, FixResult(
                        success=False,
                        original=issue.match,
                        replacement='',
                        message=f"Skipped: File discusses conscious language terms"
                    )

        # Handle different action types
        if issue.action_name == 'replace' and issue.action_params:
            replacement = issue.action_params[0]  # Use first suggestion
            return self._apply_replacement(content, issue, replacement)

        elif issue.action_name == 'edit' and issue.action_params:
            # Regex-based replacement
            return self._apply_regex_edit(content, issue)

        elif issue.check == 'RedHat.Spacing':
            # Fix double spaces
            return self._fix_double_spaces(content, issue)

        elif issue.check == 'RedHat.Using':
            # "using" -> "by using"
            return self._fix_using(content, issue)

        return content, FixResult(
            success=False,
            original=issue.match,
            replacement='',
            message=f"No automatic fix available for {issue.check}"
        )

    def _apply_replacement(self, content: str, issue: ValeIssue,
                           replacement: str) -> tuple[str, FixResult]:
        """Apply a simple text replacement."""
        lines = content.split('\n')
        line_idx = issue.line - 1

        if line_idx >= len(lines):
            return content, FixResult(
                success=False,
                original=issue.match,
                replacement=replacement,
                message=f"Line {issue.line} not found in file"
            )

        line = lines[line_idx]
        start, end = issue.span[0] - 1, issue.span[1]

        # Verify the match is what we expect
        actual_match = line[start:end]
        if actual_match.lower() != issue.match.lower():
            # Try to find the match in the line
            match_pos = line.lower().find(issue.match.lower())
            if match_pos == -1:
                return content, FixResult(
                    success=False,
                    original=issue.match,
                    replacement=replacement,
                    message=f"Could not locate '{issue.match}' in line {issue.line}"
                )
            start = match_pos
            end = match_pos + len(issue.match)
            actual_match = line[start:end]

        # Preserve case of the original
        if actual_match[0].isupper() and replacement[0].islower():
            replacement = replacement[0].upper() + replacement[1:]

        new_line = line[:start] + replacement + line[end:]
        lines[line_idx] = new_line

        return '\n'.join(lines), FixResult(
            success=True,
            original=actual_match,
            replacement=replacement,
            message=f"Replaced '{actual_match}' with '{replacement}'"
        )

    def _apply_regex_edit(self, content: str, issue: ValeIssue) -> tuple[str, FixResult]:
        """Apply a regex-based edit."""
        if len(issue.action_params) < 3:
            return content, FixResult(
                success=False,
                original=issue.match,
                replacement='',
                message="Invalid regex edit parameters"
            )

        _, pattern, replacement = issue.action_params[:3]

        lines = content.split('\n')
        line_idx = issue.line - 1

        if line_idx >= len(lines):
            return content, FixResult(
                success=False,
                original=issue.match,
                replacement='',
                message=f"Line {issue.line} not found"
            )

        line = lines[line_idx]
        new_line = re.sub(pattern, replacement, line, count=1)

        if new_line == line:
            return content, FixResult(
                success=False,
                original=issue.match,
                replacement='',
                message=f"Regex pattern did not match"
            )

        lines[line_idx] = new_line

        return '\n'.join(lines), FixResult(
            success=True,
            original=issue.match,
            replacement=re.sub(pattern, replacement, issue.match),
            message=f"Applied regex replacement"
        )

    def _fix_double_spaces(self, content: str, issue: ValeIssue) -> tuple[str, FixResult]:
        """Fix double spaces in content."""
        lines = content.split('\n')
        line_idx = issue.line - 1

        if line_idx >= len(lines):
            return content, FixResult(
                success=False,
                original=issue.match,
                replacement='',
                message=f"Line {issue.line} not found"
            )

        line = lines[line_idx]
        # Replace multiple spaces with single space
        new_line = re.sub(r'  +', ' ', line)

        if new_line == line:
            return content, FixResult(
                success=False,
                original=issue.match,
                replacement='',
                message="No double spaces found"
            )

        lines[line_idx] = new_line

        return '\n'.join(lines), FixResult(
            success=True,
            original=issue.match,
            replacement=issue.match.replace('  ', ' '),
            message="Fixed double spacing"
        )

    def _fix_using(self, content: str, issue: ValeIssue) -> tuple[str, FixResult]:
        """Fix 'using' -> 'by using' after nouns."""
        lines = content.split('\n')
        line_idx = issue.line - 1

        if line_idx >= len(lines):
            return content, FixResult(
                success=False,
                original=issue.match,
                replacement='',
                message=f"Line {issue.line} not found"
            )

        line = lines[line_idx]
        # Match pattern: word + space + using
        pattern = r'(\w+)(\s+)(using)(?=\s|$|[.,;:])'
        match = re.search(pattern, line, re.IGNORECASE)

        if not match:
            return content, FixResult(
                success=False,
                original=issue.match,
                replacement='',
                message="Could not find 'using' pattern"
            )

        # Replace "using" with "by using"
        replacement = f"{match.group(1)}{match.group(2)}by using"
        new_line = line[:match.start()] + replacement + line[match.end():]
        lines[line_idx] = new_line

        return '\n'.join(lines), FixResult(
            success=True,
            original=issue.match,
            replacement=issue.match.replace(' using', ' by using'),
            message="Changed 'using' to 'by using'"
        )

    def fix_file(self, file_path: str, issues: list[ValeIssue]) -> dict:
        """Fix all issues in a single file."""
        full_path = self.base_path / file_path

        if not full_path.exists():
            return {'error': f"File not found: {full_path}"}

        content = full_path.read_text()
        original_content = content

        # Sort issues by line number in reverse order to avoid position shifts
        sorted_issues = sorted(issues, key=lambda x: (x.line, x.span[0]), reverse=True)

        fixed_count = 0
        skipped_count = 0

        for issue in sorted_issues:
            if issue.can_auto_fix:
                content, result = self.fix_issue(issue, content)
                self.fix_results.append((issue, result))
                if result.success:
                    fixed_count += 1
                else:
                    skipped_count += 1
            else:
                self.manual_review_issues.append(issue)

        # Write changes if not dry run and content changed
        if not self.dry_run and content != original_content:
            full_path.write_text(content)

        return {
            'fixed': fixed_count,
            'skipped': skipped_count,
            'manual_review': len([i for i in issues if not i.can_auto_fix])
        }

    def fix_all(self, path: str = 'docs/') -> dict:
        """Fix all Vale issues in the specified path."""
        print(f"Running Vale on {path}...")
        vale_output = self.run_vale(path)

        if not vale_output:
            print("No issues found or Vale failed to run.")
            return {}

        self.parse_issues(vale_output)

        total_files = len(self.issues_by_file)
        total_issues = sum(len(issues) for issues in self.issues_by_file.values())

        print(f"Found {total_issues} issues in {total_files} files")
        print()

        results = {}
        for file_path, issues in self.issues_by_file.items():
            result = self.fix_file(file_path, issues)
            results[file_path] = result
            if result.get('fixed', 0) > 0:
                status = "[DRY-RUN] Would fix" if self.dry_run else "Fixed"
                print(f"  {status} {result['fixed']} issues in {file_path}")

        return results

    def generate_report(self) -> str:
        """Generate a detailed report of all issues and fixes."""
        lines = []
        lines.append("=" * 80)
        lines.append("MTA DOCUMENTATION VALE ISSUES REPORT")
        lines.append("Based on CQA 2.1 Content Quality Assessment Guidelines")
        lines.append("=" * 80)
        lines.append("")

        # Summary statistics
        total_issues = sum(len(issues) for issues in self.issues_by_file.values())
        auto_fixed = sum(1 for _, r in self.fix_results if r.success)
        manual_review = len(self.manual_review_issues)

        lines.append("SUMMARY")
        lines.append("-" * 40)
        lines.append(f"Total issues found:     {total_issues}")
        lines.append(f"Automatically fixed:    {auto_fixed}")
        lines.append(f"Need manual review:     {manual_review}")
        lines.append(f"Files affected:         {len(self.issues_by_file)}")
        lines.append("")

        # Issues by type
        issue_types = defaultdict(int)
        for file_issues in self.issues_by_file.values():
            for issue in file_issues:
                issue_types[issue.check] += 1

        lines.append("ISSUES BY TYPE")
        lines.append("-" * 40)
        for check, count in sorted(issue_types.items(), key=lambda x: -x[1]):
            lines.append(f"  {count:4d}  {check}")
        lines.append("")

        # Automatic fixes applied
        if self.fix_results:
            lines.append("AUTOMATIC FIXES APPLIED")
            lines.append("-" * 40)
            for issue, result in self.fix_results:
                if result.success:
                    lines.append(f"  {issue.file}:{issue.line}")
                    lines.append(f"    {issue.check}")
                    lines.append(f"    '{result.original}' -> '{result.replacement}'")
            lines.append("")

        # Issues requiring manual review
        if self.manual_review_issues:
            lines.append("ISSUES REQUIRING MANUAL REVIEW")
            lines.append("-" * 40)

            # Group by check type
            by_check = defaultdict(list)
            for issue in self.manual_review_issues:
                by_check[issue.check].append(issue)

            for check in sorted(by_check.keys()):
                issues = by_check[check]
                lines.append(f"\n  {check} ({len(issues)} issues)")
                lines.append("  " + "~" * 38)

                for issue in issues[:10]:  # Show first 10
                    lines.append(f"    {issue.file}:{issue.line}")
                    lines.append(f"      Match: '{issue.match}'")
                    lines.append(f"      Message: {issue.message}")

                if len(issues) > 10:
                    lines.append(f"    ... and {len(issues) - 10} more")

        lines.append("")
        lines.append("=" * 80)
        lines.append("CQA 2.1 COMPLIANCE NOTES")
        lines.append("=" * 80)
        lines.append("""
The following pre-migration requirements from CQA 2.1 are checked by Vale:

1. AsciiDocDITA checks (asciidoctor-dita-vale tool):
   - ShortDescription: Modules need [role="_abstract"] for DITA shortdesc
   - ContentType: Files need :_mod-docs-content-type: attribute
   - DocumentTitle: Files need a level 0 heading (= Title)
   - TaskContents: Procedure modules need .Procedure block title

2. RedHat style checks:
   - ConsciousLanguage: Replace master/slave, blacklist/whitelist
   - TermsErrors/TermsWarnings: Use correct terminology
   - Spelling: Verify technical terms
   - Hyphens: Correct hyphenation
   - Spacing: No double spaces
   - CaseSensitiveTerms: Use correct case for terms

Note: write-good checks (Passive, TooWordy, Weasel) are disabled as they
are too noisy for technical documentation and require manual judgment.
""")

        return '\n'.join(lines)


def main():
    parser = argparse.ArgumentParser(
        description='Fix Vale issues in MTA documentation based on CQA 2.1 guidelines',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__
    )
    parser.add_argument(
        'path',
        nargs='?',
        default='docs/',
        help='Path to scan (default: docs/)'
    )
    parser.add_argument(
        '--dry-run',
        action='store_true',
        help='Show what would be changed without making changes'
    )
    parser.add_argument(
        '--auto-fix',
        action='store_true',
        help='Automatically fix issues with clear replacements'
    )
    parser.add_argument(
        '--report-only',
        action='store_true',
        help='Only generate a report without making changes'
    )
    parser.add_argument(
        '--output',
        type=str,
        default='vale_report.txt',
        help='Output file for the report (default: vale_report.txt)'
    )
    parser.add_argument(
        '--refresh',
        action='store_true',
        help='Force re-run Vale instead of using cached output'
    )

    args = parser.parse_args()

    # Determine mode
    if args.report_only:
        dry_run = True
    elif args.auto_fix:
        dry_run = args.dry_run
    else:
        dry_run = True  # Default to dry-run for safety

    fixer = ValeIssueFixer(dry_run=dry_run, refresh=args.refresh)

    # Always run the analysis (fix_all handles dry_run mode)
    results = fixer.fix_all(args.path)

    # Always generate report
    report = fixer.generate_report()

    # Save report
    report_path = Path(args.output)
    report_path.write_text(report)
    print(f"\nReport saved to: {report_path}")

    # Print summary
    print(report)

    # Return exit code based on issues found
    if fixer.manual_review_issues:
        return 1
    return 0


if __name__ == '__main__':
    sys.exit(main())
