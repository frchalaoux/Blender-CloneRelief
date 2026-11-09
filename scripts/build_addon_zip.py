"""Build a legacy Blender add-on ZIP from the src-layout package."""

from __future__ import annotations

import argparse
from pathlib import Path
from zipfile import ZIP_DEFLATED, ZipFile


ROOT = Path(__file__).resolve().parents[1]
PACKAGE = ROOT / "src" / "clone_relief"
DEFAULT_OUTPUT = ROOT / "dist" / "blender_clone_relief_0.2.0.zip"


def build_addon_zip(output: Path) -> Path:
    """Package Python source files with the legacy add-on root folder."""
    if not PACKAGE.is_dir():
        raise FileNotFoundError(f"Add-on package directory not found: {PACKAGE}")
    output.parent.mkdir(parents=True, exist_ok=True)
    with ZipFile(output, "w", compression=ZIP_DEFLATED) as archive:
        for source in sorted(PACKAGE.glob("*.py")):
            archive.write(source, Path("clone_relief") / source.name)
    return output


def main() -> None:
    """Build a ZIP at the requested output path or the project default."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    args = parser.parse_args()
    output = build_addon_zip(args.output.resolve())
    print(f"Built {output}")


if __name__ == "__main__":
    main()
