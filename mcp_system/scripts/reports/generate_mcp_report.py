# Small wrapper to make the consolidate report script runnable from inside mcp_system/
# It locates the repository root and invokes the canonical script at <repo>/scripts/reports/generate_mcp_report.py

from __future__ import annotations
import sys
from pathlib import Path
import subprocess

def main():
    here = Path(__file__).resolve()
    # parents: 0 -> .../mcp_system/scripts/reports, 1-> .../mcp_system/scripts, 2-> .../mcp_system, 3 -> repo root
    try:
        repo_root = here.parents[3]
    except Exception:
        repo_root = here.parent.parent.parent
    target = repo_root / 'scripts' / 'reports' / 'generate_mcp_report.py'
    if not target.exists():
        print(f"Error: target script not found: {target}", file=sys.stderr)
        sys.exit(2)
    cmd = [sys.executable, str(target)] + sys.argv[1:]
    rc = subprocess.run(cmd).returncode
    sys.exit(rc)

if __name__ == '__main__':
    main()
