#!/usr/bin/env python3
"""Check local Markdown links in the maintained entry points; offline only."""
from pathlib import Path
import re
import sys
from urllib.parse import unquote

root = Path(__file__).resolve().parents[1]
pages = [root / name for name in ('README.md', 'QUICKSTART.md', 'J72-PROGRESS.md',
         'PROCESS.md', 'ROADMAP.md', 'CONTRIBUTING.md', 'code/README.md', 'history/README.md')]
pages += list((root / 'code/current').rglob('*.md'))
errors = []
for page in pages:
    for target in re.findall(r'\[[^\]]*\]\(([^\s)]+)\)', page.read_text()):
        if target.startswith(('http:', 'https:', 'mailto:', '#')):
            continue
        path = unquote(target.split('#', 1)[0])
        if path and not (page.parent / path).exists():
            errors.append(str(page.relative_to(root)) + ': ' + target)
if errors:
    print('\n'.join(errors), file=sys.stderr)
    raise SystemExit(1)
print('PASS: maintained documentation links resolve locally')
