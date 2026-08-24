from __future__ import annotations

import json
import subprocess
import sys

from mes_quant.exploration.l1_lr001 import NumericalExperimentError
from mes_quant.exploration.test2_decode import Test2DecodeContractError
from mes_quant.exploration.test2_evaluation import Test2EvaluationContractError
from mes_quant.exploration.test2_g3_contract import G3AuthorizationError
from mes_quant.exploration.test2_g3_pre_fit import G3PreFitBoundaryError
from mes_quant.exploration.test2_g3f_contract import G3FContractError
from mes_quant.exploration.test2_g3f_execution import (
    G3FExecutionBoundaryError,
    main,
)
from mes_quant.exploration.test2_l1_harness import Test2HarnessContractError
from mes_quant.exploration.test2_request_set import RequestSetContractError
from mes_quant.exploration.test2_run_context import RunContextContractError
from mes_quant.exploration.test2_target import PathTargetContractError

if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except (
        G3AuthorizationError,
        G3FContractError,
        G3FExecutionBoundaryError,
        G3PreFitBoundaryError,
        NumericalExperimentError,
        PathTargetContractError,
        RequestSetContractError,
        RunContextContractError,
        Test2DecodeContractError,
        Test2EvaluationContractError,
        Test2HarnessContractError,
        json.JSONDecodeError,
        OSError,
        subprocess.CalledProcessError,
    ) as error:
        print(f"G3F_CONDITIONAL_FIT_FAIL: {error}", file=sys.stderr)
        raise SystemExit(1) from error
