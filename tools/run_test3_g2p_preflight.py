from __future__ import annotations

import sys
from pathlib import Path


def _assert_isolated_bootstrap() -> None:
    required_flags = {
        "isolated": 1,
        "safe_path": True,
        "no_user_site": 1,
        "ignore_environment": 1,
        "dont_write_bytecode": 1,
    }
    for field, expected in required_flags.items():
        if getattr(sys.flags, field, None) != expected:
            raise RuntimeError(f"Test 3 G2-P requires .venv/bin/python -I -B ({field})")
    forbidden_entries = {"", str(Path.cwd()), str(Path.cwd() / "tools")}
    if forbidden_entries.intersection(sys.path):
        raise RuntimeError("Test 3 G2-P isolated sys.path contains cwd or tools")


def run() -> int:
    _assert_isolated_bootstrap()
    from mes_quant.exploration.test3_g2p_preflight import (
        main,
        write_failure_summary_if_consumed,
    )

    try:
        return main()
    except Exception as error:  # noqa: BLE001 - preserve any consumed authorization failure
        failure = write_failure_summary_if_consumed(
            project_root=Path.cwd(),
            error=error,
        )
        if failure is not None:
            print(f"TEST3_G2P_FAILURE_SUMMARY={failure}", file=sys.stderr)
        print(f"TEST3_G2P_PREFLIGHT_FAIL: {error}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(run())
