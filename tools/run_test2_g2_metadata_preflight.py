from __future__ import annotations

import json
import subprocess
import sys

from mes_quant.exploration.test2_l1_harness import Test2HarnessContractError
from mes_quant.exploration.test2_metadata_preflight import G2BoundaryError, main

if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except (
        G2BoundaryError,
        Test2HarnessContractError,
        json.JSONDecodeError,
        OSError,
        subprocess.CalledProcessError,
    ) as error:
        print(f"G2_METADATA_PREFLIGHT_FAIL: {error}", file=sys.stderr)
        raise SystemExit(1) from error
