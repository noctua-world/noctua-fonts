#!/usr/bin/env python3
"""Run every check of this repository. Run it before every commit.

    ./tools/check.py
    ./tools/check.py --release

The first checks the tests, the site, and the fonts that are present; the
second does the same, but every font in SHA256SUMS must be present.

What it runs, in order, each with the Python that runs this script:

1. The test suite: `python -m unittest discover -s tests -t .`. The tests build
   their fonts in memory with fontTools, so fontTools and brotli must be
   importable, and they read the build plan with tomllib, so the Python must
   be 3.11 or later. When either is missing, this script says so and stops,
   rather than letting test modules fail to import.
2. `site/build.py --check`: site/public/, the published specimen site, must be
   exactly what site/ generates. A difference means someone edited site/public/
   by hand or forgot to rebuild.
3. `tools/font-archives.py verify --allow-missing`: every font present must
   match SHA256SUMS and every font present must be listed there. A fresh clone
   has no fonts, and that is not an error. With --release, a missing font is an
   error too (`verify` without --allow-missing), and `tools/font-archives.py
   list` must show every font in exactly one archive: run it before
   `tools/font-archives.py pack`.

Every step runs from the repository root, the folder above this script's.

Exit status 0 when every step passes, 1 otherwise. Every step runs even when an
earlier one fails, so one run reports everything.

Standard library only; works on Linux, macOS and Windows. Nothing here reaches
the network or writes to the repository.
"""

from __future__ import annotations

import argparse
import importlib.util
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent


def missing_modules() -> list[str]:
    return [name for name in ("fontTools", "brotli") if importlib.util.find_spec(name) is None]


def run(title: str, args: list[str]) -> bool:
    print(f"\n== {title}", flush=True)
    result = subprocess.run([sys.executable, *args], cwd=ROOT)
    passed = result.returncode == 0
    print(f"== {title}: {'ok' if passed else f'FAILED (exit status {result.returncode})'}", flush=True)
    return passed


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Run every check of this repository: the tests, the site, the fonts.")
    parser.add_argument("--release", action="store_true",
                        help="require every font in SHA256SUMS to be present, and every font to "
                             "belong to exactly one archive (run before tools/font-archives.py pack)")
    options = parser.parse_args()

    if sys.version_info < (3, 11):
        print(f"error: this Python ({sys.executable}) is {sys.version.split()[0]}; the tests need "
              "3.11 or later, for tomllib. The tools themselves run on 3.9 or later. Make the "
              "virtual environment with a newer python3.", file=sys.stderr)
        return 1

    missing = missing_modules()
    if missing:
        print(f"error: this Python ({sys.executable}) cannot import {' and '.join(missing)}, "
              "which the tests need. In a virtual environment, from the repository root:\n\n"
              "    python3 -m venv .venv\n"
              "    .venv/bin/python -m pip install fonttools brotli\n"
              "    .venv/bin/python tools/check.py\n\n"
              "On Windows the last two are .venv\\Scripts\\python -m pip install fonttools brotli "
              "and .venv\\Scripts\\python tools\\check.py.\n", file=sys.stderr)
        return 1

    results = {
        "tests": run("tests", ["-m", "unittest", "discover", "-s", "tests", "-t", "."]),
        "site": run("site: site/public/ matches site/", ["site/build.py", "--check"]),
    }
    if options.release:
        results["fonts"] = run("fonts: every font present and matching SHA256SUMS",
                               ["tools/font-archives.py", "verify"])
        results["archives"] = run("archives: every font in exactly one archive",
                                  ["tools/font-archives.py", "list"])
    else:
        results["fonts"] = run("fonts: the fonts present match SHA256SUMS",
                               ["tools/font-archives.py", "verify", "--allow-missing"])

    failed = [name for name, passed in results.items() if not passed]
    print()
    if failed:
        print(f"check FAILED: {', '.join(failed)}")
        return 1
    print("check passed")
    return 0


if __name__ == "__main__":
    sys.exit(main())
