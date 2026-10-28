from __future__ import annotations

import argparse
import subprocess
import sys


def main() -> None:
    parser = argparse.ArgumentParser(description="Run the full thesis review workflow.")
    parser.add_argument("--docx", help="Path to thesis DOCX")
    parser.add_argument("--pdf", help="Path to thesis PDF")
    parser.add_argument("--output-dir", default="guide_checker/output", help="Directory for outputs")
    args = parser.parse_args()

    command = [
        sys.executable,
        "-X",
        "utf8",
        "-m",
        "guide_checker.cli.run_full_review",
        "--output-dir",
        args.output_dir,
    ]
    if args.docx:
        command.extend(["--docx", args.docx])
    if args.pdf:
        command.extend(["--pdf", args.pdf])
    raise SystemExit(subprocess.call(command))


if __name__ == "__main__":
    main()
