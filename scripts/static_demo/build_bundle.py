"""Bundle the Python packages for the in-browser demo (GitHub Pages).

Usage (from the repository root)::

    python scripts/static_demo/build_bundle.py [--out frontend/public/py/agentpause-py.zip]

The zip holds the pure-Python packages ``agentpause``, ``agentpause_sim`` and ``app`` (with
their data files) plus ``agentpause_web.py``. The web app's worker unpacks it into Pyodide.
"""

from __future__ import annotations

import argparse
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
PACKAGES = {
    "agentpause": ROOT / "sdk" / "python" / "src" / "agentpause",
    "agentpause_sim": ROOT / "simulator" / "src" / "agentpause_sim",
    "app": ROOT / "backend" / "app",
}
SKIP_DIRS = {"__pycache__", "tests"}


def build(out: Path) -> Path:
    out.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(out, "w", compression=zipfile.ZIP_DEFLATED) as zf:
        for name, source in PACKAGES.items():
            for path in sorted(source.rglob("*")):
                if path.is_dir() or SKIP_DIRS.intersection(path.relative_to(source).parts) or path.suffix == ".pyc":
                    continue
                zf.write(path, Path(name) / path.relative_to(source))
        zf.write(Path(__file__).with_name("agentpause_web.py"), "agentpause_web.py")
    return out


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__.split("\n", 1)[0])
    parser.add_argument("--out", type=Path, default=ROOT / "frontend" / "public" / "py" / "agentpause-py.zip")
    args = parser.parse_args()
    path = build(args.out)
    print(f"wrote {path} ({path.stat().st_size / 1024:.0f} KB)")


if __name__ == "__main__":
    main()
