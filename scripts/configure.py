import re
import sys
from pathlib import Path

if len(sys.argv) != 2 or not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9-]{0,38}", sys.argv[1]):
    raise SystemExit("Usage: python scripts/configure.py YOUR_GITHUB_USERNAME")

readme = Path(__file__).resolve().parents[1] / "README.md"
readme.write_text(readme.read_text().replace("YOUR_USERNAME", sys.argv[1].lower()))
print("README configured for repository ai381-lab2")
