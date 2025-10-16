from pathlib import Path
import re

text = Path("alembic/versions/20251004_vps_platform.py").read_text(encoding="utf-8")
match = re.search(r"op.create_table\(\"workers\".*?\n\s*\)\n", text, re.DOTALL)
if match:
    print(match.group(0))
else:
    print("not-found")
