from __future__ import annotations

import ast
import hashlib
import subprocess
from datetime import UTC, datetime
from pathlib import Path

import pytest

from mes_quant.exploration import test3_design
from mes_quant.exploration.test3_design import (
    SyntheticPredictorRequest,
    build_synthetic_predictor_ledger,
)

_PROJECT_ROOT = Path(__file__).parents[1]
_FROZEN_L0_COMMIT = "b16d025dd84b590a8a441c05232e6f761ee7f9bf"
_FROZEN_L0_SHA256 = "44e398497c57559fd8700daa33f087ce290aa5264cbd143d7ea4cd2311581ae9"
_PREDECESSOR_G2P_COMMIT = "485bfa16a6567b5c54e91b7cc72e7f1be58775a9"
_PREDECESSOR_G2P_SHA256 = "015c35dc3673c2741b2cd2eaedb295e129f3f4b45ae382f1b2e5e83e248cf935"
_G2P_PATH = "src/mes_quant/exploration/test3_g2p_preflight.py"


class _HistoricalInvalidEvidence(RuntimeError):
    def __init__(self, category: str) -> None:
        self.category = category
        super().__init__(category)


def _git_blob(commit: str, path: str) -> bytes:
    return subprocess.run(
        ["git", "show", f"{commit}:{path}"],
        cwd=_PROJECT_ROOT,
        check=True,
        capture_output=True,
    ).stdout


def _historical_normalized_identity():
    source = _git_blob(_PREDECESSOR_G2P_COMMIT, _G2P_PATH)
    assert hashlib.sha256(source).hexdigest() == _PREDECESSOR_G2P_SHA256
    tree = ast.parse(source.decode("utf-8"))
    function = next(
        node
        for node in tree.body
        if isinstance(node, ast.FunctionDef) and node.name == "_normalized_identity"
    )

    def invalid_evidence(category: str) -> None:
        raise _HistoricalInvalidEvidence(category)

    namespace = {"_invalid_evidence": invalid_evidence}
    isolated = ast.Module(body=[function], type_ignores=[])
    ast.fix_missing_locations(isolated)
    exec(compile(isolated, _G2P_PATH, "exec"), namespace)  # noqa: S102
    return namespace["_normalized_identity"]


def test_pipe_identity_proves_predecessor_nonconformance_to_frozen_l0() -> None:
    frozen_l0 = _git_blob(
        _FROZEN_L0_COMMIT,
        "src/mes_quant/exploration/test3_design.py",
    )
    assert hashlib.sha256(frozen_l0).hexdigest() == _FROZEN_L0_SHA256
    assert hashlib.sha256(Path(test3_design.__file__).read_bytes()).hexdigest() == (
        _FROZEN_L0_SHA256
    )

    identity = "SYNTH|ID"
    decision_time = datetime(2023, 1, 3, 15, 0, tzinfo=UTC)
    ledger = build_synthetic_predictor_ledger(
        [SyntheticPredictorRequest(identity, decision_time, 1.0, 1.0, 1.0)]
    )
    assert ledger.rows[0].decision_identity == identity
    assert ledger.rows[0].status == "PREDICTOR_USABLE"
    expected_payload = (
        f"{identity}|{decision_time.isoformat()}|PREDICTOR_USABLE\n".encode()
    )
    assert ledger.ordered_status_sha256 == hashlib.sha256(expected_payload).hexdigest()

    historical = _historical_normalized_identity()
    with pytest.raises(_HistoricalInvalidEvidence) as observed:
        historical(identity)
    assert observed.value.category == "DECISION_ID_LEDGER_HASH_DELIMITER_PRESENT"
