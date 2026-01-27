#!/usr/bin/env python3
"""
replace_shared_snippets.py - Process shared snippets in MTA documentation

This script finds snippet files and can:
1. List all snippet files and their usage
2. Inline snippet content directly into including documents
3. Validate that all snippets are properly referenced

Adapted for MTA (Migration Toolkit for Applications) documentation structure.

Snippet Identification:
- Files with `:_mod-docs-content-type: SNIPPET` header
- Files with `:_content-type: SNIPPET` header
- Files with 'snippet' in the name (snippet_*, snippet-*, *-snippet.adoc)
- Files in a `snippets/` subdirectory
- Files starting with `// snippet` comment
"""

import argparse
import logging
import os
import re
import sys
from pathlib import Path
from typing import Dict, List, Optional, Set, Tuple

# Configure logging
logging.basicConfig(
    format='%(levelname)s: %(message)s',
    level=logging.INFO,
    stream=sys.stdout
)
log = logging.getLogger(__name__)

# Regular expressions for AsciiDoc processing
INCLUDE_RE = re.compile(r'^include::([^\[]+)\[(.*?)\]', re.MULTILINE)

# Snippet identification patterns
SNIPPET_NAME_PATTERNS = [
    re.compile(r'^snippet[_-].*\.adoc$', re.IGNORECASE),  # snippet_*.adoc, snippet-*.adoc
    re.compile(r'.*[_-]snippet\.adoc$', re.IGNORECASE),   # *-snippet.adoc, *_snippet.adoc
]

# Header patterns that identify snippet files
SNIPPET_HEADER_PATTERNS = [
    re.compile(r'^:_mod-docs-content-type:\s*SNIPPET', re.MULTILINE | re.IGNORECASE),
    re.compile(r'^:_content-type:\s*SNIPPET', re.MULTILINE | re.IGNORECASE),
    re.compile(r'^//\s*snippet\s*$', re.MULTILINE | re.IGNORECASE),
]

# Default paths for MTA documentation
DEFAULT_DOCS_DIR = "docs"
DEFAULT_TOPICS_DIR = "docs/topics"
DEFAULT_ASSEMBLIES_DIR = "assemblies"


def is_snippet_by_name(filename: str) -> bool:
    """Check if a file is a snippet based on its filename."""
    return any(pattern.match(filename) for pattern in SNIPPET_NAME_PATTERNS)


def is_snippet_by_content(filepath: Path) -> bool:
    """Check if a file is a snippet based on its content headers."""
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read(500)  # Read first 500 chars for header check
        return any(pattern.search(content) for pattern in SNIPPET_HEADER_PATTERNS)
    except Exception as e:
        log.warning(f"Could not read {filepath}: {e}")
        return False


def is_in_snippets_dir(filepath: Path) -> bool:
    """Check if a file is located in a snippets directory."""
    return 'snippets' in filepath.parts


def find_snippet_files(base_dir: Path, include_all_dirs: bool = True) -> List[Path]:
    """
    Find all snippet files in the documentation directory.
    
    Snippets are identified by:
    - Filename containing 'snippet' pattern (snippet_*, snippet-*, *-snippet.adoc)
    - Being in a 'snippets/' directory
    - Containing snippet content-type headers
    - Starting with `// snippet` comment
    
    Args:
        base_dir: Base directory to search
        include_all_dirs: If True, search all subdirectories; otherwise only docs/topics
    """
    snippets: Set[Path] = set()
    processed_files: Set[Path] = set()  # Track processed files to handle symlinks
    search_paths = []
    
    if include_all_dirs:
        search_paths = [base_dir]
    else:
        # Only search specific documentation directories
        topics_dir = base_dir / DEFAULT_TOPICS_DIR
        assemblies_dir = base_dir / DEFAULT_ASSEMBLIES_DIR
        search_paths = [p for p in [topics_dir, assemblies_dir] if p.exists()]
    
    for search_path in search_paths:
        for root, dirs, files in os.walk(search_path, followlinks=True):
            # Skip build/output directories
            dirs[:] = [d for d in dirs if d not in ('build', '_site', 'tmp', 'website')]
            
            for filename in files:
                if not filename.endswith('.adoc'):
                    continue
                    
                filepath = Path(root) / filename
                resolved_path = filepath.resolve()
                
                # Skip already-processed files (handles symlinks)
                if resolved_path in processed_files:
                    continue
                processed_files.add(resolved_path)
                
                # Check various snippet identification methods
                if is_snippet_by_name(filename):
                    snippets.add(resolved_path)
                    continue
                    
                if is_in_snippets_dir(filepath):
                    snippets.add(resolved_path)
                    continue
                    
                if is_snippet_by_content(filepath):
                    snippets.add(resolved_path)
    
    return sorted(snippets)


def find_snippet_usage(base_dir: Path, snippets: List[Path]) -> Dict[Path, List[Tuple[Path, str, int]]]:
    """
    Find where each snippet is used (included) in the documentation.
    
    Returns a dict mapping snippet path to list of (including_file, include_line, line_number) tuples.
    """
    usage: Dict[Path, List[Tuple[Path, str, int]]] = {snippet: [] for snippet in snippets}
    snippet_names = {snippet.name: snippet for snippet in snippets}
    processed_files: Set[Path] = set()  # Track already-processed files to avoid duplicates from symlinks
    
    search_paths = [
        base_dir / DEFAULT_DOCS_DIR,
        base_dir / DEFAULT_ASSEMBLIES_DIR,
    ]
    
    for search_path in search_paths:
        if not search_path.exists():
            continue
            
        for root, dirs, files in os.walk(search_path, followlinks=True):
            # Skip build/output directories
            dirs[:] = [d for d in dirs if d not in ('build', '_site', 'tmp', 'website')]
            
            for filename in files:
                if not filename.endswith('.adoc'):
                    continue
                    
                filepath = Path(root) / filename
                resolved_path = filepath.resolve()
                
                # Skip already-processed files (handles symlinks)
                if resolved_path in processed_files:
                    continue
                processed_files.add(resolved_path)
                
                # Skip snippet files themselves
                if resolved_path in snippets:
                    continue
                
                try:
                    with open(filepath, 'r', encoding='utf-8') as f:
                        lines = f.readlines()
                    
                    for line_num, line in enumerate(lines, 1):
                        match = INCLUDE_RE.match(line)
                        if match:
                            include_path = match.group(1)
                            include_name = Path(include_path).name
                            
                            if include_name in snippet_names:
                                snippet = snippet_names[include_name]
                                usage[snippet].append((resolved_path, match.group(0), line_num))
                                
                except Exception as e:
                    log.warning(f"Could not read {filepath}: {e}")
    
    return usage


def read_snippet_content(snippet_path: Path, strip_headers: bool = True) -> str:
    """
    Read snippet file content, optionally stripping metadata headers.
    
    Args:
        snippet_path: Path to the snippet file
        strip_headers: If True, remove content-type headers and snippet comments
    """
    with open(snippet_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    if strip_headers:
        # Remove content-type headers
        for pattern in SNIPPET_HEADER_PATTERNS:
            content = pattern.sub('', content)
    
    # Strip leading/trailing whitespace but preserve internal formatting
    return content.strip()


def adjust_heading_levels(content: str, offset: int) -> str:
    """
    Adjust AsciiDoc heading levels by the given offset.
    """
    if offset == 0:
        return content
    
    def adjust_heading(match):
        equals = match.group(1)
        rest = match.group(2)
        new_level = '=' * (len(equals) + offset)
        return f"{new_level}{rest}"
    
    # Match headings at the start of a line
    return re.sub(r'^(=+)(.*)$', adjust_heading, content, flags=re.MULTILINE)


def inline_snippet(including_file: Path, snippet_path: Path, snippet_content: str,
                   dry_run: bool = False) -> bool:
    """
    Replace an include directive with the actual snippet content.
    
    Returns True if replacement was made.
    """
    try:
        with open(including_file, 'r', encoding='utf-8') as f:
            content = f.read()
    except Exception as e:
        log.error(f"Could not read {including_file}: {e}")
        return False
    
    snippet_name = snippet_path.name
    
    # Find and replace the include directive
    # Match include::path/to/snippet_file.adoc[options]
    pattern = re.compile(
        rf'^include::([^\[]*{re.escape(snippet_name)})\[(.*?)\]',
        re.MULTILINE
    )
    
    def replace_include(match):
        options = match.group(2)
        # Handle leveloffset if present
        leveloffset_match = re.search(r'leveloffset=\+?(\d+)', options)
        if leveloffset_match:
            offset = int(leveloffset_match.group(1))
            # Adjust heading levels in snippet content
            adjusted_content = adjust_heading_levels(snippet_content, offset)
            return adjusted_content
        return snippet_content
    
    new_content = pattern.sub(replace_include, content)
    
    if new_content != content:
        if dry_run:
            log.info(f"Would inline {snippet_name} in {including_file}")
        else:
            with open(including_file, 'w', encoding='utf-8') as f:
                f.write(new_content)
            log.info(f"Inlined {snippet_name} in {including_file}")
        return True
    
    return False


def list_snippets_command(args):
    """Handle the 'list' subcommand."""
    base_dir = Path(args.base_dir).resolve()
    
    if not base_dir.exists():
        log.error(f"Base directory not found: {base_dir}")
        return 1
    
    snippets = find_snippet_files(base_dir)
    
    if not snippets:
        log.info("No snippet files found.")
        return 0
    
    print(f"\nFound {len(snippets)} snippet file(s):\n")
    
    if args.show_usage:
        usage = find_snippet_usage(base_dir, snippets)
        for snippet in snippets:
            uses = usage[snippet]
            try:
                relative_path = snippet.relative_to(base_dir)
            except ValueError:
                relative_path = snippet
            
            # Determine how the snippet was identified
            identification = []
            if is_snippet_by_name(snippet.name):
                identification.append("name")
            if is_in_snippets_dir(snippet):
                identification.append("snippets dir")
            if is_snippet_by_content(snippet):
                identification.append("header")
            
            id_str = f" [{', '.join(identification)}]" if identification else ""
            print(f"  {relative_path}{id_str}")
            
            if uses:
                print(f"    Used in {len(uses)} location(s):")
                for including_file, include_line, line_num in uses:
                    try:
                        rel_inc = including_file.relative_to(base_dir)
                    except ValueError:
                        rel_inc = including_file
                    print(f"      - {rel_inc}:{line_num}")
            else:
                print("    ⚠ Not used in any files")
            print()
    else:
        for snippet in snippets:
            try:
                relative_path = snippet.relative_to(base_dir)
            except ValueError:
                relative_path = snippet
            print(f"  {relative_path}")
    
    return 0


def inline_command(args):
    """Handle the 'inline' subcommand."""
    base_dir = Path(args.base_dir).resolve()
    
    if not base_dir.exists():
        log.error(f"Base directory not found: {base_dir}")
        return 1
    
    snippets = find_snippet_files(base_dir)
    
    if not snippets:
        log.info("No snippet files found.")
        return 0
    
    usage = find_snippet_usage(base_dir, snippets)
    
    # Filter to specific snippet if provided
    if args.snippet:
        target_snippets = [s for s in snippets if args.snippet in s.name]
        if not target_snippets:
            log.error(f"Snippet not found: {args.snippet}")
            return 1
    else:
        target_snippets = snippets
    
    replaced_count = 0
    for snippet in target_snippets:
        uses = usage[snippet]
        if not uses:
            continue
            
        snippet_content = read_snippet_content(snippet, strip_headers=not args.keep_headers)
        
        for including_file, _, _ in uses:
            if inline_snippet(including_file, snippet, snippet_content, args.dry_run):
                replaced_count += 1
    
    if args.dry_run:
        print(f"\nWould replace {replaced_count} include(s)")
    else:
        print(f"\nReplaced {replaced_count} include(s)")
        
        if args.delete_snippets and not args.dry_run:
            deleted = 0
            for snippet in target_snippets:
                if usage[snippet]:  # Only delete if it was used
                    try:
                        os.remove(snippet)
                        log.info(f"Deleted snippet file: {snippet}")
                        deleted += 1
                    except Exception as e:
                        log.error(f"Could not delete {snippet}: {e}")
            print(f"Deleted {deleted} snippet file(s)")
    
    return 0


def validate_command(args):
    """Handle the 'validate' subcommand."""
    base_dir = Path(args.base_dir).resolve()
    
    if not base_dir.exists():
        log.error(f"Base directory not found: {base_dir}")
        return 1
    
    snippets = find_snippet_files(base_dir)
    usage = find_snippet_usage(base_dir, snippets)
    
    errors = []
    warnings = []
    
    # Check for unused snippets
    for snippet, uses in usage.items():
        if not uses:
            try:
                rel_path = snippet.relative_to(base_dir)
            except ValueError:
                rel_path = snippet
            warnings.append(f"Unused snippet: {rel_path}")
    
    # Check for broken snippet includes
    search_paths = [
        base_dir / DEFAULT_DOCS_DIR,
        base_dir / DEFAULT_ASSEMBLIES_DIR,
    ]
    
    for search_path in search_paths:
        if not search_path.exists():
            continue
            
        for root, dirs, files in os.walk(search_path, followlinks=True):
            dirs[:] = [d for d in dirs if d not in ('build', '_site', 'tmp', 'website')]
            
            for filename in files:
                if not filename.endswith('.adoc'):
                    continue
                
                filepath = Path(root) / filename
                try:
                    with open(filepath, 'r', encoding='utf-8') as f:
                        content = f.read()
                    
                    for match in INCLUDE_RE.finditer(content):
                        include_path = match.group(1)
                        include_name = Path(include_path).name
                        
                        # Check if this looks like a snippet include
                        if is_snippet_by_name(include_name) or 'snippet' in include_path.lower():
                            # Check if the file exists
                            full_path = (filepath.parent / include_path).resolve()
                            if not full_path.exists():
                                try:
                                    rel_filepath = filepath.relative_to(base_dir)
                                except ValueError:
                                    rel_filepath = filepath
                                errors.append(f"Broken snippet include in {rel_filepath}: {include_path}")
                            
                except Exception as e:
                    log.warning(f"Could not read {filepath}: {e}")
    
    # Print results
    print(f"\nValidation Results for {base_dir}:")
    print(f"  Snippets found: {len(snippets)}")
    print(f"  Errors: {len(errors)}")
    print(f"  Warnings: {len(warnings)}")
    
    if errors:
        print("\nErrors:")
        for error in errors:
            print(f"  ❌ {error}")
    
    if warnings:
        print("\nWarnings:")
        for warning in warnings:
            print(f"  ⚠ {warning}")
    
    if not errors and not warnings:
        print("\n✅ All snippets are valid and in use.")
    
    return 1 if errors else 0


def show_command(args):
    """Handle the 'show' subcommand - display snippet content."""
    base_dir = Path(args.base_dir).resolve()
    
    if not base_dir.exists():
        log.error(f"Base directory not found: {base_dir}")
        return 1
    
    snippets = find_snippet_files(base_dir)
    
    # Find matching snippet
    matching = [s for s in snippets if args.snippet in s.name]
    
    if not matching:
        log.error(f"Snippet not found: {args.snippet}")
        print("\nAvailable snippets:")
        for s in snippets:
            print(f"  - {s.name}")
        return 1
    
    for snippet in matching:
        try:
            relative_path = snippet.relative_to(base_dir)
        except ValueError:
            relative_path = snippet
            
        print(f"\n{'='*60}")
        print(f"File: {relative_path}")
        print('='*60)
        
        content = read_snippet_content(snippet, strip_headers=False)
        print(content)
        print()
    
    return 0


def setup_parser() -> argparse.ArgumentParser:
    """Set up command-line argument parser."""
    parser = argparse.ArgumentParser(
        description="Process shared snippets in MTA documentation",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # List all snippet files
  python replace_shared_snippets.py list
  
  # List snippets with usage information
  python replace_shared_snippets.py list --show-usage
  
  # Show contents of a specific snippet
  python replace_shared_snippets.py show developer-preview-admonition
  
  # Inline all snippets (dry run)
  python replace_shared_snippets.py inline --dry-run
  
  # Inline a specific snippet
  python replace_shared_snippets.py inline --snippet technology-preview-admonition.adoc
  
  # Inline snippets and delete the original files
  python replace_shared_snippets.py inline --delete-snippets
  
  # Validate snippet references
  python replace_shared_snippets.py validate

Snippet Identification:
  Snippets are identified by any of the following:
  - Filename: snippet_*.adoc, snippet-*.adoc, *-snippet.adoc
  - Location: files in a 'snippets/' subdirectory
  - Header: :_mod-docs-content-type: SNIPPET
  - Header: :_content-type: SNIPPET
  - Comment: // snippet (at start of file)
"""
    )
    
    parser.add_argument(
        '--base-dir',
        default='.',
        help='Base directory of the MTA documentation repository (default: current directory)'
    )
    parser.add_argument(
        '-v', '--verbose',
        action='store_true',
        help='Enable verbose output'
    )
    
    subparsers = parser.add_subparsers(dest='command', help='Available commands')
    
    # List command
    list_parser = subparsers.add_parser('list', help='List all snippet files')
    list_parser.add_argument(
        '--show-usage', '-u',
        action='store_true',
        help='Show where each snippet is used'
    )
    
    # Show command
    show_parser = subparsers.add_parser('show', help='Show contents of a snippet file')
    show_parser.add_argument(
        'snippet',
        help='Name (or partial name) of the snippet to show'
    )
    
    # Inline command
    inline_parser = subparsers.add_parser('inline', help='Inline snippets into including files')
    inline_parser.add_argument(
        '--dry-run', '-n',
        action='store_true',
        help='Show what would be done without making changes'
    )
    inline_parser.add_argument(
        '--snippet', '-s',
        help='Process only the specified snippet file (partial name match)'
    )
    inline_parser.add_argument(
        '--keep-headers',
        action='store_true',
        help='Keep snippet content-type headers when inlining'
    )
    inline_parser.add_argument(
        '--delete-snippets',
        action='store_true',
        help='Delete snippet files after inlining'
    )
    
    # Validate command
    validate_parser = subparsers.add_parser('validate', help='Validate snippet references')
    
    return parser


def main():
    parser = setup_parser()
    args = parser.parse_args()
    
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)
    
    if args.command == 'list':
        return list_snippets_command(args)
    elif args.command == 'show':
        return show_command(args)
    elif args.command == 'inline':
        return inline_command(args)
    elif args.command == 'validate':
        return validate_command(args)
    else:
        parser.print_help()
        return 0


if __name__ == "__main__":
    sys.exit(main())
