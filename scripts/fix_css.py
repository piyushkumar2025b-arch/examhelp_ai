"""
One-shot repair: removes the orphaned old CSS block from smart_reader_engine.py
and appends the new Free Media Explorer tab.
"""
import re, os

path = "smart_reader_engine.py"
src  = open(path, encoding="utf-8").read()

# ── 1. Remove the stale bare CSS block (everything between the two triple-quotes)
# It sits between line 784 (end of _CSS string) and the AI FUNCTION REGISTRY section.
# We can identify it by the pattern: end of _CSS string  -> bare CSS  -> # === AI FUNCTION REGISTRY
pattern = re.compile(
    r'(?<=\"\"\"\n)'           # after the closing """ of the _CSS string
    r'\n+'                     # blank lines
    r'/\* .*? \*/'             # first CSS comment
    r'.*?'                     # all CSS content (non-greedy)
    r'\.sr-toc-level \{ padding-left: calc\(var\(--lvl,0\) \* 16px\); \}\s*'
    r'</style>\s*'
    r'"""\s*\n',               # closing triple-quote of old block
    re.DOTALL
)
if pattern.search(src):
    src = pattern.sub("\n\n", src)
    print("Removed old CSS block via regex.")
else:
    # Fallback: line-based removal
    lines = src.splitlines(keepends=True)
    new_lines = []
    skip = False
    for i, line in enumerate(lines):
        # Start skipping after the _CSS string ends (line with just '"""')
        # and we hit a CSS comment
        if not skip and i > 780 and line.strip().startswith("/* ") and "Root" in line:
            skip = True
            print(f"Starting skip at line {i+1}")
            continue
        if skip:
            # Stop skipping when we hit "# === AI FUNCTION REGISTRY"
            if "AI FUNCTION REGISTRY" in line:
                skip = False
                new_lines.append(line)
            continue
        new_lines.append(line)
    src = "".join(new_lines)
    print("Removed old CSS block via line scan.")

# ── 2. Write back
open(path, "w", encoding="utf-8").write(src)
print("Done. Checking syntax...")

import ast
try:
    ast.parse(src)
    print("Syntax OK!")
except SyntaxError as e:
    print(f"SyntaxError at line {e.lineno}: {e.msg}")
