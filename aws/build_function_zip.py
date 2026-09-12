"""Build the Lambda function deployment zip from the project's own code."""

import zipfile
from pathlib import Path

PROJECT_ROOT = Path(__file__).parent.parent
OUTPUT_ZIP = Path(__file__).parent / "vera-function.zip"

FILES = [
    "data_source.py",
    "calle_cli.py",
    "templates.py",
    "tools.py",
    "bootstrap.py",
    "lambda_handler.py",
    "mock_residents.json",
]


def main() -> None:
    if OUTPUT_ZIP.exists():
        OUTPUT_ZIP.unlink()
    with zipfile.ZipFile(OUTPUT_ZIP, "w", zipfile.ZIP_DEFLATED) as zf:
        for name in FILES:
            zf.write(PROJECT_ROOT / name, arcname=name)
    print(f"Wrote {OUTPUT_ZIP} ({OUTPUT_ZIP.stat().st_size} bytes, {len(FILES)} files)")


if __name__ == "__main__":
    main()
