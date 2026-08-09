"""Extract immutable code-cell references from the canonical Colab export.

This utility is intentionally limited to reference material. Production modules
must never import the extracted notebook cells.
"""

from __future__ import annotations

import argparse
import hashlib
import json
from collections.abc import Iterable
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
REFERENCE_DIR = PROJECT_ROOT / "reference" / "colab_v1_cells_0_13"
NOTEBOOK_PATH = REFERENCE_DIR / "MES_V1_cells_0_13.ipynb"


def sha256_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def normalized_source(source: str) -> str:
    return source.replace("\r\n", "\n").replace("\r", "\n").rstrip() + "\n"


def ensure_reference_outputs_writable(
    output_paths: Iterable[Path], *, replace_existing_reference: bool
) -> None:
    """Refuse to mutate any existing frozen output unless explicitly authorized."""

    existing = sorted(path.name for path in output_paths if path.exists())
    if existing and not replace_existing_reference:
        raise RuntimeError(
            "Frozen reference outputs already exist and are create-only: "
            + ", ".join(existing)
            + ". Use --replace-existing-reference only for an approved reference-version bump."
        )


def _parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--replace-existing-reference",
        action="store_true",
        help=(
            "replace existing frozen outputs; reserved for an explicitly approved "
            "reference-version bump"
        ),
    )
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> None:
    args = _parse_args(argv)
    output_paths = [REFERENCE_DIR / f"cell{index:02d}.py" for index in range(14)]
    output_paths.extend(
        [REFERENCE_DIR / "SHA256SUMS.txt", REFERENCE_DIR / "cell_sources_manifest.json"]
    )
    ensure_reference_outputs_writable(
        output_paths, replace_existing_reference=args.replace_existing_reference
    )

    notebook = json.loads(NOTEBOOK_PATH.read_text(encoding="utf-8"))
    cells = notebook.get("cells", [])
    if len(cells) != 14:
        raise RuntimeError(f"Expected 14 cells, found {len(cells)}")

    manifest_cells: list[dict[str, object]] = []
    checksum_lines: list[str] = []

    for index, cell in enumerate(cells):
        if cell.get("cell_type") != "code":
            raise RuntimeError(f"Cell {index} is not a code cell")
        source = normalized_source("".join(cell.get("source", [])))
        output_path = REFERENCE_DIR / f"cell{index:02d}.py"
        output_path.write_text(source, encoding="utf-8", newline="\n")
        digest = sha256_bytes(source.encode("utf-8"))
        checksum_lines.append(f"{digest}  {output_path.name}")
        manifest_cells.append(
            {
                "cell": index,
                "execution_count": cell.get("execution_count"),
                "source_file": output_path.name,
                "normalized_source_sha256": digest,
                "source_lines": len(source.splitlines()),
            }
        )

    notebook_bytes = NOTEBOOK_PATH.read_bytes()
    notebook_digest = sha256_bytes(notebook_bytes)
    checksum_lines.insert(0, f"{notebook_digest}  {NOTEBOOK_PATH.name}")
    (REFERENCE_DIR / "SHA256SUMS.txt").write_text(
        "\n".join(checksum_lines) + "\n", encoding="utf-8", newline="\n"
    )
    (REFERENCE_DIR / "cell_sources_manifest.json").write_text(
        json.dumps(
            {
                "reference_version": "COLAB_CELLS_0_13_V1",
                "notebook_file": NOTEBOOK_PATH.name,
                "notebook_local_sha256": notebook_digest,
                "cell_order": list(range(14)),
                "execution_counts": [cell["execution_count"] for cell in manifest_cells],
                "cells": manifest_cells,
            },
            indent=2,
            sort_keys=True,
        )
        + "\n",
        encoding="utf-8",
        newline="\n",
    )

    print(f"PASS: extracted {len(manifest_cells)} cells from {NOTEBOOK_PATH.name}")


if __name__ == "__main__":
    main()
