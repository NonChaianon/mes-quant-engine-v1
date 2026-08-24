from __future__ import annotations

import sys
from pathlib import Path

from mes_quant.exploration.test3_metadata_preflight import (
    main,
    write_failure_summary_if_consumed,
)


def run() -> int:
    try:
        return main()
    except Exception as error:  # noqa: BLE001 - must preserve any consumed failure
        failure = write_failure_summary_if_consumed(
            project_root=Path.cwd(),
            error=error,
        )
        if failure is not None:
            print(
                f"TEST3_G2_FAILURE_SUMMARY={failure}",
                file=sys.stderr,
            )
        print(f"TEST3_G2_METADATA_PREFLIGHT_FAIL: {error}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(run())
