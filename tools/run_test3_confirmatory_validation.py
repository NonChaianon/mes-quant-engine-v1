"""Fixed synthetic self-check for the Test 3 confirmatory-validation implementation.

Classification:
``IMPLEMENTATION_CAPABILITY_ONLY / NOT_C0 / NOT_C0V / NOT_RATIFICATION /
NOT_ACTIVATION``

Result label. Every line this runner emits, on success and on failure alike, is
prefixed with ``LOCAL_SYNTHETIC_DATA_FREE_IMPLEMENTATION_ONLY``. A guard refuses
to emit any line containing a claim token, so no output of this runner can be
read as activation, an execution or scoring checkpoint, a reservation, a fit
permit, evidence, a Validation opening, a witness, a terminal class, or a
scientific result of any kind. A completed self-check states only that fixed
synthetic mechanics reproduced themselves and matched the ratified tooling
binding.

Closed command line. The runner accepts the single literal token
``--self-check`` and nothing else: no input path, no output path, no data,
provider, target or evidence path operand, no repository path, no configuration
flag and no environment-supplied value. Every scientific operand it uses is a
closed-form synthetic constant produced by the implementation module itself.

Reads and writes. The runner writes nothing at all: no file, no directory, no
record and no repository mutation of any kind. It reads exactly two governed
files, both located from this file's own resolved position and never from an
argument, an environment value, ``sys.path`` or the working directory:

1. ``src/mes_quant/exploration/test3_confirmatory_validation.py``; and
2. ``docs/research/TEST3_CONFIRMATORY_VALIDATION_TOOLING_BINDING_V1.json``.

Launch and origin discipline. The only successful invocation uses the current
interpreter with both ``-B`` and ``-I`` and the absolute runner path. Before
reading either governed file or importing NumPy, the runner proves the live
isolated/safe-path/no-bytecode flags and its own non-symlink lexical origin. It
then imports a previously uncached NumPy from the current interpreter's
``site-packages``, verifies its package, linalg and random origins, compares the
complete live runtime identity with the ratified binding, and revalidates the
same module objects/origins/version after loading the implementation source.

Exit codes: ``0`` when every named check passes, ``2`` for any refusal or
failure.
"""

from __future__ import annotations

import hashlib
import importlib
import importlib.util
import json
import math
import platform
import stat
import sys
from datetime import UTC, datetime, timedelta
from pathlib import Path
from typing import Any

RUNNER_NAME = "run_test3_confirmatory_validation"
RUNNER_SOURCE_NAME = "run_test3_confirmatory_validation.py"
SELF_CHECK_MODE = "--self-check"
CANONICAL_INTERPRETER_FLAGS: tuple[str, ...] = ("-B", "-I")
CLASSIFICATION = (
    "IMPLEMENTATION_CAPABILITY_ONLY / NOT_C0 / NOT_C0V / NOT_RATIFICATION / NOT_ACTIVATION"
)

RESULT_LABEL = "LOCAL_SYNTHETIC_DATA_FREE_IMPLEMENTATION_ONLY"
SELF_CHECK_COMPLETE_TOKEN = "SELF_CHECK_COMPLETE_ALL_NAMED_SYNTHETIC_CHECKS_REPRODUCED"
LOCAL_RUNTIME_ORIGIN_DISPOSITION = (
    "LOCAL_RUNTIME_ORIGIN_OBSERVED_AND_RECHECKED_NOT_RATIFIED_ORIGIN"
)
NO_CLAIM_TOKEN = (
    "THIS_OUTPUT_IS_NOT_ACTIVATION_NOT_AN_EXECUTION_OR_SCORING_CHECKPOINT_"
    "NOT_A_RESERVATION_NOT_A_FIT_PERMIT_NOT_A_WITNESS_NO_OWNER_GRANT_2_"
    "NO_C0V_VALIDATION_REMAINS_UNOPENED_AND_ASSERTS_NO_SCIENTIFIC_RESULT"
)

RUNNER_GUARANTEES: tuple[str, ...] = (
    "EXACTLY_ONE_FIXED_SYNTHETIC_SELF_CHECK_MODE",
    "NO_INPUT_PATH_OPERAND",
    "NO_OUTPUT_PATH_OPERAND",
    "NO_DATA_PROVIDER_OR_TARGET_PATH_OPERAND",
    "NO_EVIDENCE_PATH_OPERAND",
    "NO_REPOSITORY_WRITE_OF_ANY_KIND",
    "REQUIRES_ISOLATED_SAFE_PATH_AND_NO_BYTECODE_INTERPRETER_FLAGS",
    "NO_NETWORK",
    "READS_ONLY_ITS_OWN_GOVERNED_IMPLEMENTATION_SOURCE_AND_THE_RATIFIED_TOOLING_BINDING",
    "LOCAL_RUNTIME_ORIGIN_OBSERVED_AND_RECHECKED_NOT_RATIFIED_ORIGIN",
    "NO_ACTIVATION_AND_NO_RUNTIME_CHECKPOINT_AUTHORITY",
    "NO_OWNER_GRANT_2_AND_NO_C0V",
    "NO_RESERVATION_AND_NO_FIT_PERMIT",
    "VALIDATION_REMAINS_UNOPENED_AND_NO_WITNESS_IS_MADE",
    "FINAL_TEST_REMAINS_SEALED",
    "ASSERTS_NO_SCIENTIFIC_RESULT",
)

# Substrings that would turn an emitted line into a claim. Each is a positive
# assertion form; none of them appears in this runner's own vocabulary, so the
# guard can be applied to every line without exempting the disclaimers.
FORBIDDEN_RESULT_CLAIM_TOKENS: tuple[str, ...] = (
    "ACTIVATED",
    "ACTIVATION_GRANTED",
    "ACTIVATION_CREATED",
    "C0_ESTABLISHED",
    "C0V_ESTABLISHED",
    "C0_GRANTED",
    "C0V_GRANTED",
    "RESERVATION_CREATED",
    "RESERVATION_ISSUED",
    "PERMIT_ISSUED",
    "PERMIT_GRANTED",
    "PERMIT_CONSUMED",
    "EVIDENCE_CREATED",
    "EVIDENCE_RECORDED",
    "EVIDENCE_WRITTEN",
    "VALIDATION_OPENED",
    "VALIDATION_OPENING",
    "WITNESS_CREATED",
    "CONFIRMED_ON_OUTER_VALIDATION",
    "FINAL_TEST_OPENED",
    "INVALID_EVIDENCE",
    "UNDERPOWERED_STOP",
    "SCIENTIFIC_SUCCESS",
    "SCIENTIFICALLY_CONFIRMED",
    "HYPOTHESIS_CONFIRMED",
    "GRANT_1_ISSUED",
    "GRANT_2_ISSUED",
)

ERROR_CODES: tuple[str, ...] = (
    "ARGUMENTS_NONCONFORMING",
    "STARTUP_FLAGS_NONCONFORMING",
    "RUNNER_ORIGIN_NONCONFORMING",
    "NUMPY_CACHE_NONCONFORMING",
    "NUMPY_ORIGIN_NONCONFORMING",
    "RUNTIME_IDENTITY_NONCONFORMING",
    "MODULE_CACHE_NONCONFORMING",
    "IMPLEMENTATION_ORIGIN_NONCONFORMING",
    "RATIFIED_BINDING_ORIGIN_NONCONFORMING",
    "IMPLEMENTATION_IMPORT_NONCONFORMING",
    "RESULT_LABEL_NONCONFORMING",
    "INTERNAL_NONCONFORMANCE",
    "SELF_CHECK_FAILED",
)

numpy: Any = None
_NUMPY_SNAPSHOT: tuple[Any, ...] | None = None


class RunnerRefusal(RuntimeError):
    """One stable machine-coded refusal; the runner never raises a raw traceback."""

    def __init__(self, code: str, detail: str) -> None:
        super().__init__(f"{code}: {detail}")
        self.code = code
        self.detail = detail


# --------------------------------------------------------------------------
# Result labelling and the claim guard
# --------------------------------------------------------------------------


def assert_no_claim(text: str) -> str:
    """Refuse any text that would read as a claim rather than a synthetic check."""

    if not isinstance(text, str):
        raise RunnerRefusal("RESULT_LABEL_NONCONFORMING", "emitted text must be a string")
    upper = text.upper()
    for token in FORBIDDEN_RESULT_CLAIM_TOKENS:
        if token in upper:
            raise RunnerRefusal(
                "RESULT_LABEL_NONCONFORMING",
                f"a result line may never contain the claim token {token}",
            )
    return text


def labelled(text: str) -> str:
    """Prefix one line with the mandatory result label, after the claim guard."""

    return f"{RESULT_LABEL}: {RUNNER_NAME}: {assert_no_claim(text)}"


def _emit(stream: Any, text: str) -> None:
    stream.write(labelled(text) + "\n")


# --------------------------------------------------------------------------
# Closed argument surface
# --------------------------------------------------------------------------


def parse_arguments(argv: object) -> str:
    """Accept exactly ``['--self-check']`` and refuse every other argument vector.

    There is no second mode, no operand, no flag value and no path. Any extra
    token, any missing token, any equals form and any alternative spelling is a
    refusal, so no caller can steer this runner at a repository, data, provider,
    target or evidence surface.
    """

    if isinstance(argv, (str, bytes)) or not isinstance(argv, (list, tuple)):
        raise RunnerRefusal(
            "ARGUMENTS_NONCONFORMING", "arguments must be supplied as a sequence of tokens"
        )
    arguments = list(argv)
    if len(arguments) != 1:
        raise RunnerRefusal(
            "ARGUMENTS_NONCONFORMING",
            f"exactly one token is accepted and it must be {SELF_CHECK_MODE}",
        )
    token = arguments[0]
    if not isinstance(token, str) or token != SELF_CHECK_MODE:
        raise RunnerRefusal(
            "ARGUMENTS_NONCONFORMING",
            "the only accepted token is the fixed synthetic self-check mode; "
            "no input path, output path or external operand is accepted",
        )
    return SELF_CHECK_MODE


# --------------------------------------------------------------------------
# Governed origin resolution
# --------------------------------------------------------------------------


IMPLEMENTATION_SOURCE_PARTS: tuple[str, ...] = (
    "src",
    "mes_quant",
    "exploration",
    "test3_confirmatory_validation.py",
)
RATIFIED_BINDING_PARTS: tuple[str, ...] = (
    "docs",
    "research",
    "TEST3_CONFIRMATORY_VALIDATION_TOOLING_BINDING_V1.json",
)
IMPLEMENTATION_MODULE_NAME = "mes_quant_test3_confirmatory_validation_implementation"
EXPECTED_MODULE_ID = "MES_TEST3_CONFIRMATORY_VALIDATION_IMPLEMENTATION_V1"


def _lexical_runner_path() -> Path:
    """Validate the executing runner and every parent without resolving links."""

    raw = Path(__file__)
    if not raw.is_absolute() or raw.name != RUNNER_SOURCE_NAME:
        raise RunnerRefusal(
            "RUNNER_ORIGIN_NONCONFORMING",
            "the runner must be invoked by its absolute governed source path",
        )
    current = Path(raw.anchor)
    parts = raw.parts[1:]
    try:
        for position, part in enumerate(parts):
            current = current / part
            entry = current.lstat()
            if stat.S_ISLNK(entry.st_mode):
                raise RunnerRefusal(
                    "RUNNER_ORIGIN_NONCONFORMING",
                    "the runner path or one of its parents is a symlink",
                )
            final = position == len(parts) - 1
            if final and not stat.S_ISREG(entry.st_mode):
                raise RunnerRefusal(
                    "RUNNER_ORIGIN_NONCONFORMING", "the runner origin is not a regular file"
                )
            if not final and not stat.S_ISDIR(entry.st_mode):
                raise RunnerRefusal(
                    "RUNNER_ORIGIN_NONCONFORMING", "a runner parent is not a directory"
                )
    except RunnerRefusal:
        raise
    except OSError as error:
        raise RunnerRefusal(
            "RUNNER_ORIGIN_NONCONFORMING",
            f"the runner path cannot be inspected: {type(error).__name__}",
        ) from None
    return raw


def require_hardened_startup() -> Path:
    """Require real ``-B -I`` semantics before any governed read or NumPy import."""

    if (
        sys.flags.isolated != 1
        or sys.flags.safe_path != 1
        or sys.flags.dont_write_bytecode != 1
        or not sys.dont_write_bytecode
    ):
        raise RunnerRefusal(
            "STARTUP_FLAGS_NONCONFORMING",
            "the runner requires the current interpreter with -B -I",
        )
    runner = _lexical_runner_path()
    if not sys.argv or Path(sys.argv[0]) != runner:
        raise RunnerRefusal(
            "STARTUP_FLAGS_NONCONFORMING",
            "the absolute governed runner must be the interpreter script operand",
        )
    root = runner.parent.parent
    forbidden = {root, runner.parent, Path.cwd()}
    for entry in sys.path:
        if not isinstance(entry, str) or not entry:
            raise RunnerRefusal(
                "STARTUP_FLAGS_NONCONFORMING", "sys.path contains an empty or non-text entry"
            )
        candidate = Path(entry)
        try:
            observed = candidate.resolve(strict=True)
        except OSError:
            continue
        if observed in forbidden or root in observed.parents:
            raise RunnerRefusal(
                "STARTUP_FLAGS_NONCONFORMING",
                "sys.path exposes the worktree, runner directory or current directory",
            )
    return root


def runner_root() -> Path:
    """Derive the root from the already validated non-symlink lexical path."""

    return _lexical_runner_path().parent.parent


def _regular_non_symlink_origin(value: Any, *, package_root: Path | None = None) -> Path:
    """Validate one imported module origin without accepting a symlink."""

    if not isinstance(value, str) or not value:
        raise RunnerRefusal("NUMPY_ORIGIN_NONCONFORMING", "a NumPy origin is absent")
    path = Path(value)
    if not path.is_absolute():
        raise RunnerRefusal("NUMPY_ORIGIN_NONCONFORMING", "a NumPy origin is not absolute")
    try:
        entry = path.lstat()
    except OSError as error:
        raise RunnerRefusal(
            "NUMPY_ORIGIN_NONCONFORMING",
            f"a NumPy origin cannot be inspected: {type(error).__name__}",
        ) from None
    if stat.S_ISLNK(entry.st_mode) or not stat.S_ISREG(entry.st_mode):
        raise RunnerRefusal(
            "NUMPY_ORIGIN_NONCONFORMING", "a NumPy origin is not a non-symlink regular file"
        )
    if path.resolve(strict=True) != path:
        raise RunnerRefusal(
            "NUMPY_ORIGIN_NONCONFORMING", "a NumPy origin resolves through substitution"
        )
    if package_root is not None and package_root not in path.parents:
        raise RunnerRefusal(
            "NUMPY_ORIGIN_NONCONFORMING", "a NumPy submodule is outside the package root"
        )
    return path


def load_trusted_numpy() -> Any:
    """Import an uncached NumPy and snapshot its trusted local origins."""

    global _NUMPY_SNAPSHOT, numpy
    if any(name == "numpy" or name.startswith("numpy.") for name in sys.modules):
        raise RunnerRefusal(
            "NUMPY_CACHE_NONCONFORMING", "NumPy or a NumPy submodule was preloaded"
        )
    try:
        loaded = importlib.import_module("numpy")
        linalg = importlib.import_module("numpy.linalg")
        random = importlib.import_module("numpy.random")
    except Exception as error:  # noqa: BLE001 - map every import failure to one refusal.
        raise RunnerRefusal(
            "NUMPY_ORIGIN_NONCONFORMING", f"NumPy import failed: {type(error).__name__}"
        ) from None
    root_file = _regular_non_symlink_origin(getattr(loaded, "__file__", None))
    root = root_file.parent
    prefix = Path(sys.prefix).resolve(strict=True)
    if prefix not in root.parents or "site-packages" not in root.parts:
        raise RunnerRefusal(
            "NUMPY_ORIGIN_NONCONFORMING",
            "NumPy is not under this interpreter environment's site-packages",
        )
    package_path = tuple(str(Path(item)) for item in getattr(loaded, "__path__", ()))
    spec = getattr(loaded, "__spec__", None)
    search_locations = getattr(spec, "submodule_search_locations", ()) or ()
    spec_locations = tuple(str(Path(item)) for item in search_locations)
    if package_path != (str(root),) or spec_locations != package_path:
        raise RunnerRefusal(
            "NUMPY_ORIGIN_NONCONFORMING", "NumPy package search locations are nonconforming"
        )
    origins: list[str] = []
    for module in (loaded, linalg, random):
        file_path = _regular_non_symlink_origin(
            getattr(module, "__file__", None), package_root=root
        )
        spec_origin = getattr(getattr(module, "__spec__", None), "origin", None)
        if spec_origin != str(file_path):
            raise RunnerRefusal(
                "NUMPY_ORIGIN_NONCONFORMING", "NumPy __file__ and spec origin differ"
            )
        origins.append(str(file_path))
    numpy = loaded
    _NUMPY_SNAPSHOT = (loaded, linalg, random, tuple(origins), str(loaded.__version__), root)
    return loaded


def revalidate_numpy_snapshot() -> None:
    """Reject cache, origin or version drift after implementation loading."""

    if _NUMPY_SNAPSHOT is None:
        raise RunnerRefusal("NUMPY_CACHE_NONCONFORMING", "NumPy was not snapshotted")
    loaded, linalg, random, origins, version, root = _NUMPY_SNAPSHOT
    for name, expected in (("numpy", loaded), ("numpy.linalg", linalg), ("numpy.random", random)):
        if sys.modules.get(name) is not expected:
            raise RunnerRefusal(
                "NUMPY_CACHE_NONCONFORMING", "a trusted NumPy cache entry was replaced"
            )
    observed: list[str] = []
    package_path = tuple(str(Path(item)) for item in getattr(loaded, "__path__", ()))
    search_locations = getattr(
        getattr(loaded, "__spec__", None), "submodule_search_locations", ()
    ) or ()
    spec_locations = tuple(str(Path(item)) for item in search_locations)
    if package_path != (str(root),) or spec_locations != package_path:
        raise RunnerRefusal(
            "NUMPY_ORIGIN_NONCONFORMING", "NumPy package search locations drifted"
        )
    for module in (loaded, linalg, random):
        path = _regular_non_symlink_origin(
            getattr(module, "__file__", None), package_root=root
        )
        if getattr(getattr(module, "__spec__", None), "origin", None) != str(path):
            raise RunnerRefusal(
                "NUMPY_ORIGIN_NONCONFORMING", "a NumPy origin drifted after import"
            )
        observed.append(str(path))
    if tuple(observed) != origins or str(loaded.__version__) != version:
        raise RunnerRefusal(
            "NUMPY_ORIGIN_NONCONFORMING", "NumPy origin or version drifted after import"
        )


def _runtime_json_safe(value: Any) -> Any:
    if isinstance(value, dict):
        return {str(key): _runtime_json_safe(item) for key, item in value.items()}
    if isinstance(value, (list, tuple)):
        return [_runtime_json_safe(item) for item in value]
    if value is None or isinstance(value, (bool, int, float, str)):
        return value
    return str(value)


def _numpy_build_config() -> Any:
    config = getattr(numpy, "__config__", None)
    show = getattr(config, "show", None)
    if callable(show):
        try:
            observed = show(mode="dicts")
        except TypeError:
            observed = None
        if observed:
            return _runtime_json_safe(observed)
    legacy = {
        name: getattr(config, name)
        for name in dir(config)
        if name.endswith("_info")
    }
    if not legacy:
        raise RunnerRefusal(
            "RUNTIME_IDENTITY_NONCONFORMING", "NumPy build configuration is unavailable"
        )
    return _runtime_json_safe(legacy)


def live_runtime_identity() -> dict[str, Any]:
    """Build the exact identity shape used by the ratified prerequisite tool."""

    float_fields = ("epsilon", "max", "min")
    float_int_fields = (
        "dig",
        "mant_dig",
        "max_10_exp",
        "max_exp",
        "min_10_exp",
        "min_exp",
        "radix",
        "rounds",
    )
    float64_hex_fields = ("eps", "epsneg", "tiny", "max", "min", "resolution")
    float64_int_fields = ("nmant", "nexp", "machep", "negep", "iexp", "maxexp", "minexp")
    executable = Path(sys.executable)
    resolved_executable = executable.resolve(strict=True)
    info = sys.float_info
    float_info = {
        **{f"{name}_hex": float(getattr(info, name)).hex() for name in float_fields},
        **{name: int(getattr(info, name)) for name in float_int_fields},
    }
    finfo = numpy.finfo(numpy.float64)
    dtype = numpy.dtype(numpy.float64)
    generator = numpy.random.default_rng(0)
    bit_generator = generator.bit_generator
    return {
        "python": {
            "implementation": platform.python_implementation(),
            "version": platform.python_version(),
            "version_full": sys.version,
            "api_version": sys.api_version,
            "hexversion": sys.hexversion,
            "cache_tag": str(sys.implementation.cache_tag),
            "maxsize": sys.maxsize,
            "float_repr_style": sys.float_repr_style,
            "executable": sys.executable,
            "executable_resolved": str(resolved_executable),
            "float_info": float_info,
        },
        "numpy": {"version": str(numpy.__version__), "build_config": _numpy_build_config()},
        "platform": {
            "system": platform.system(),
            "release": platform.release(),
            "version": platform.version(),
            "machine": platform.machine(),
            "processor": platform.processor(),
            "byteorder": sys.byteorder,
            "libc": list(platform.libc_ver()),
        },
        "float64": {
            "dtype_str": dtype.str,
            "itemsize": int(dtype.itemsize),
            "byteorder": dtype.byteorder,
            **{
                f"{name}_hex": float(getattr(finfo, name)).hex()
                for name in float64_hex_fields
            },
            **{name: int(getattr(finfo, name)) for name in float64_int_fields},
        },
        "rng": {
            "bit_generator_module": type(bit_generator).__module__,
            "bit_generator_class": type(bit_generator).__qualname__,
            "generator_class": f"{type(generator).__module__}.{type(generator).__qualname__}",
            "pcg64_module": numpy.random.PCG64.__module__,
            "pcg64_class": numpy.random.PCG64.__qualname__,
        },
    }


def require_ratified_runtime_identity(binding_bytes: bytes) -> None:
    """Compare the complete live identity with the ratified binding exactly."""

    try:
        document = json.loads(binding_bytes.decode("utf-8"))
        expected = document["payload"]["runtime_identity_binding"]["identity"]
    except (KeyError, TypeError, ValueError, UnicodeError):
        raise RunnerRefusal(
            "RUNTIME_IDENTITY_NONCONFORMING", "the ratified runtime identity is unavailable"
        ) from None
    observed = live_runtime_identity()
    if observed != expected:
        raise RunnerRefusal(
            "RUNTIME_IDENTITY_NONCONFORMING",
            "the complete live Python/NumPy/platform/float64/RNG identity differs",
        )


def resolve_governed_file(parts: tuple[str, ...], code: str) -> Path:
    """Resolve one governed file and refuse a symlinked or substituted origin."""

    root = runner_root()
    walked = root
    for part in parts:
        walked = walked / part
        if walked.is_symlink():
            raise RunnerRefusal(code, f"a governed path component is a symlink: {part}")
    candidate = root.joinpath(*parts)
    if candidate.resolve() != candidate:
        raise RunnerRefusal(code, "the governed path resolves to a substituted origin")
    if not candidate.is_file():
        raise RunnerRefusal(code, "the governed file is absent")
    if not stat.S_ISREG(candidate.lstat().st_mode):
        raise RunnerRefusal(code, "the governed path is not a regular file")
    return candidate


def read_ratified_binding_bytes() -> bytes:
    """Read the exact bytes of the ratified tooling-binding document."""

    path = resolve_governed_file(RATIFIED_BINDING_PARTS, "RATIFIED_BINDING_ORIGIN_NONCONFORMING")
    try:
        return path.read_bytes()
    except OSError as error:
        raise RunnerRefusal(
            "RATIFIED_BINDING_ORIGIN_NONCONFORMING",
            f"cannot read the ratified tooling binding: {type(error).__name__}",
        ) from None


def implementation_module() -> Any:
    """Load the implementation module alone, from its own verified source file.

    A module already present in ``sys.modules`` under this runner's private name
    is refused outright: a preloaded or forged cache entry is never reused. The
    surrounding package is deliberately not imported, so running this self-check
    pulls in no third-party data, table, storage or provider dependency.
    """

    if IMPLEMENTATION_MODULE_NAME in sys.modules:
        raise RunnerRefusal(
            "MODULE_CACHE_NONCONFORMING",
            "a module is already cached under the private implementation name",
        )
    source = resolve_governed_file(
        IMPLEMENTATION_SOURCE_PARTS, "IMPLEMENTATION_ORIGIN_NONCONFORMING"
    )
    try:
        before = source.read_bytes()
    except OSError as error:
        raise RunnerRefusal(
            "IMPLEMENTATION_ORIGIN_NONCONFORMING",
            f"cannot read the implementation source: {type(error).__name__}",
        ) from None
    digest_before = hashlib.sha256(before).hexdigest()

    module: Any = None
    try:
        spec = importlib.util.spec_from_file_location(IMPLEMENTATION_MODULE_NAME, source)
        if spec is None or spec.loader is None:
            raise ImportError("no loader for the confirmatory implementation source")
        if spec.origin != str(source):
            raise ImportError("the module spec origin is not the governed source path")
        module = importlib.util.module_from_spec(spec)
        sys.modules[IMPLEMENTATION_MODULE_NAME] = module
        spec.loader.exec_module(module)
    except Exception as error:  # noqa: BLE001 - map every loader failure to one refusal.
        sys.modules.pop(IMPLEMENTATION_MODULE_NAME, None)
        raise RunnerRefusal(
            "IMPLEMENTATION_IMPORT_NONCONFORMING",
            f"cannot load the confirmatory implementation: {type(error).__name__}",
        ) from None

    try:
        after = source.read_bytes()
        if hashlib.sha256(after).hexdigest() != digest_before:
            raise RunnerRefusal(
                "IMPLEMENTATION_ORIGIN_NONCONFORMING",
                "the implementation source changed while it was being loaded",
            )
        if sys.modules.get(IMPLEMENTATION_MODULE_NAME) is not module:
            raise RunnerRefusal(
                "MODULE_CACHE_NONCONFORMING",
                "the cached module was replaced during load",
            )
        origin = getattr(getattr(module, "__spec__", None), "origin", None)
        file_attribute = getattr(module, "__file__", None)
        if (
            getattr(module, "__name__", None) != IMPLEMENTATION_MODULE_NAME
            or origin != str(source)
            or file_attribute is None
            or Path(file_attribute).resolve() != source
        ):
            raise RunnerRefusal(
                "IMPLEMENTATION_ORIGIN_NONCONFORMING",
                "the loaded module does not report the governed source origin",
            )
        if (
            getattr(module, "MODULE_ID", None) != EXPECTED_MODULE_ID
            or getattr(module, "CLASSIFICATION", None) != CLASSIFICATION
        ):
            raise RunnerRefusal(
                "IMPLEMENTATION_ORIGIN_NONCONFORMING",
                "the loaded module does not carry the expected frozen identity",
            )
    except RunnerRefusal:
        sys.modules.pop(IMPLEMENTATION_MODULE_NAME, None)
        raise
    except OSError:
        sys.modules.pop(IMPLEMENTATION_MODULE_NAME, None)
        raise RunnerRefusal(
            "IMPLEMENTATION_ORIGIN_NONCONFORMING",
            "the implementation source could not be re-read after load",
        ) from None
    return module


# --------------------------------------------------------------------------
# Fixed synthetic operands
# --------------------------------------------------------------------------


def synthetic_runtime_identity(marker: str) -> dict[str, Any]:
    """Build one closed-schema synthetic runtime identity.

    Every value is invented and fixed. Nothing is read from the live
    interpreter, NumPy build, platform or filesystem, so this record can never
    be mistaken for a real execution or scoring runtime binding.
    """

    return {
        "python": {
            "implementation": "SyntheticPython",
            "version": "0.0.0",
            "version_full": f"SyntheticPython 0.0.0 {marker}",
            "api_version": 0,
            "hexversion": 0,
            "cache_tag": "synthetic-0",
            "maxsize": 1,
            "float_repr_style": "short",
            "executable": "/synthetic/bin/python",
            "executable_resolved": "/synthetic/bin/python",
            "float_info": {
                "epsilon_hex": float(2.0**-52).hex(),
                "max_hex": (1.0).hex(),
                "min_hex": (0.5).hex(),
                "dig": 15,
                "mant_dig": 53,
                "max_10_exp": 308,
                "max_exp": 1024,
                "min_10_exp": -307,
                "min_exp": -1021,
                "radix": 2,
                "rounds": 1,
            },
        },
        "numpy": {
            "version": "0.0.0",
            "build_config": {"blas": "synthetic", "lapack": "synthetic"},
        },
        "platform": {
            "system": "Synthetic",
            "release": "0",
            "version": "0",
            "machine": "synthetic",
            "processor": "",
            "byteorder": "little",
            "libc": ["synthetic", "0"],
        },
        "float64": {
            "dtype_str": "<f8",
            "itemsize": 8,
            "byteorder": "=",
            "eps_hex": float(2.0**-52).hex(),
            "epsneg_hex": float(2.0**-53).hex(),
            "tiny_hex": float(2.0**-1022).hex(),
            "max_hex": (1.0).hex(),
            "min_hex": (-1.0).hex(),
            "resolution_hex": (1e-15).hex(),
            "nmant": 52,
            "nexp": 11,
            "machep": -52,
            "negep": -53,
            "iexp": 11,
            "maxexp": 1024,
            "minexp": -1021,
        },
        "rng": {
            "bit_generator_module": "synthetic.random._pcg64",
            "bit_generator_class": "PCG64",
            "generator_class": "synthetic.random.Generator",
            "pcg64_module": "synthetic.random._pcg64",
            "pcg64_class": "PCG64",
        },
    }


def synthetic_train_columns(count: int) -> dict[str, numpy.ndarray]:
    """Build the fixed synthetic ordered ``float64`` feature columns."""

    index = numpy.arange(count, dtype=numpy.float64)
    slot = index % 24.0
    angle = 2.0 * math.pi * slot / 24.0
    return {
        "intercept": numpy.ones(count, dtype=numpy.float64),
        "X60": 0.10 + 0.010 * ((index * 7.0) % 11.0),
        "X120": 0.20 + 0.011 * ((index * 5.0) % 13.0),
        "X240": 0.30 + 0.012 * ((index * 3.0) % 17.0),
        "SESSION_SIN": numpy.sin(angle),
        "SESSION_COS": numpy.cos(angle),
        "WOBBLE": 0.01 * (((index * 11.0) % 7.0) - 3.0),
    }


def synthetic_row_identities(count: int) -> tuple[str, ...]:
    """Build fixed, unique, ordered synthetic common-eligible row identities."""

    return tuple(f"SYNTHETIC_TRAIN_ROW_{position:04d}" for position in range(count))


def _design_matrix(columns: dict[str, numpy.ndarray], names: tuple[str, ...]) -> numpy.ndarray:
    return numpy.ascontiguousarray(
        numpy.column_stack([columns[name] for name in names]), dtype=numpy.float64
    )


def synthetic_train_sample(module: Any, count: int = 120) -> Any:
    """Bind one fixed synthetic common-eligible TRAIN sample for both models."""

    columns = synthetic_train_columns(count)
    identities = synthetic_row_identities(count)
    log_target = numpy.ascontiguousarray(
        0.50
        + 0.30 * columns["X60"]
        + 0.20 * columns["X120"]
        + 0.10 * columns["X240"]
        + 0.05 * columns["SESSION_SIN"]
        - 0.04 * columns["SESSION_COS"]
        + columns["WOBBLE"],
        dtype=numpy.float64,
    )
    designs = [
        module.bind_deployment_design(
            model_id,
            module.MODEL_COLUMNS[model_id],
            identities,
            _design_matrix(columns, module.MODEL_COLUMNS[model_id]),
        )
        for model_id in module.MODEL_ORDER
    ]
    return module.bind_common_eligible_train_sample(identities, log_target, designs)


def synthetic_rank_deficient_sample(module: Any, count: int = 120) -> Any:
    """Bind one fixed synthetic sample whose BASE design is rank deficient."""

    columns = synthetic_train_columns(count)
    identities = synthetic_row_identities(count)
    log_target = numpy.ascontiguousarray(columns["X60"] + 0.5, dtype=numpy.float64)
    duplicated = dict(columns)
    duplicated["SESSION_SIN"] = columns["intercept"]
    duplicated["SESSION_COS"] = columns["intercept"]
    designs = [
        module.bind_deployment_design(
            model_id,
            module.MODEL_COLUMNS[model_id],
            identities,
            _design_matrix(duplicated, module.MODEL_COLUMNS[model_id]),
        )
        for model_id in module.MODEL_ORDER
    ]
    return module.bind_common_eligible_train_sample(identities, log_target, designs)


def synthetic_mismatched_identity_sample(module: Any, count: int = 120) -> Any:
    """Build one sample whose HAR rows are not the shared common-eligible rows."""

    columns = synthetic_train_columns(count)
    identities = synthetic_row_identities(count)
    shifted = tuple(f"OTHER_{name}" for name in identities)
    log_target = numpy.ascontiguousarray(columns["X60"] + 0.5, dtype=numpy.float64)
    base = module.bind_deployment_design(
        module.BASE_MODEL_ID,
        module.MODEL_COLUMNS[module.BASE_MODEL_ID],
        identities,
        _design_matrix(columns, module.MODEL_COLUMNS[module.BASE_MODEL_ID]),
    )
    har = module.bind_deployment_design(
        module.HAR_MODEL_ID,
        module.MODEL_COLUMNS[module.HAR_MODEL_ID],
        shifted,
        _design_matrix(columns, module.MODEL_COLUMNS[module.HAR_MODEL_ID]),
    )
    return module.CommonEligibleTrainSample(
        row_identities=identities, log_target=log_target, designs=(base, har)
    )


def synthetic_scoring_design(module: Any, model_id: str, sample: Any) -> Any:
    """Return the bound design of one model from a bound synthetic sample."""

    for design in sample.designs:
        if design.model_id == model_id:
            return design
    raise RunnerRefusal("INTERNAL_NONCONFORMANCE", "the synthetic sample is incomplete")


def synthetic_acf_rows(
    module: Any, *, constant: bool, sessions: int = 3, interleaved: bool = False
) -> tuple[Any, ...]:
    """Build fixed 15-minute-spaced synthetic ACF rows in strict chronological order."""

    start = datetime(2024, 1, 2, 15, 0, tzinfo=UTC)
    rows = []
    for session in range(sessions):
        session_start = start + timedelta(days=session)
        for step in range(12):
            value = 1.0 if constant else 1.0 + ((session * 12 + step) % 5) / 8.0
            identity = f"SYNTHETIC_ACF_SESSION_{session:02d}"
            if interleaved and step % 2 == 1:
                identity = "SYNTHETIC_ACF_SESSION_ALT"
            rows.append(
                module.AcfRow(
                    session_id=identity,
                    decision_time=session_start + timedelta(minutes=15 * step),
                    rv_fwd_60=value,
                )
            )
    return tuple(rows)


# --------------------------------------------------------------------------
# The one fixed synthetic self-check
# --------------------------------------------------------------------------


def _check(name: str, passed: bool, detail: str = "") -> tuple[str, bool, str]:
    assert_no_claim(name)
    assert_no_claim(detail)
    return (name, bool(passed), detail)


def _golden_checks(
    module: Any, binding_bytes: bytes, checks: list[tuple[str, bool, str]]
) -> Any:
    verification = module.verify_golden_projection_against_ratified_binding(binding_bytes)
    checks.append(
        _check(
            "RATIFIED_GOLDEN_BINDING_BYTEWISE_MATCH",
            verification.verified
            and not verification.replay_mismatches
            and not verification.binding_mismatches
            and verification.binding_schema == module.RATIFIED_TOOLING_BINDING_SCHEMA
            and not module.golden_binding_refusal_reasons(verification),
            f"binding_document_sha256={verification.binding_document_sha256}",
        )
    )
    mutated = bytearray(binding_bytes)
    mutated[-2] = mutated[-2] ^ 0x01
    tampered = module.verify_golden_projection_against_ratified_binding(bytes(mutated))
    checks.append(
        _check(
            "A_ONE_BYTE_MUTATION_OF_THE_RATIFIED_BINDING_IS_REFUSED",
            not tampered.verified
            and bool(tampered.binding_mismatches)
            and bool(module.golden_binding_refusal_reasons(tampered)),
            "a mutated binding is refused before any comparison is trusted",
        )
    )
    return verification


def _bootstrap_checks(
    module: Any, verification: Any, checks: list[tuple[str, bool, str]]
) -> None:
    record, _raw = module.build_golden_projection()
    blocks = list(record["blocks_ordered"])
    checks.append(
        _check(
            "FROZEN_BOOTSTRAP_BLOCK_ORDER_AND_SEEDS",
            tuple(item["block_length"] for item in blocks)
            == module.BOOTSTRAP_BLOCK_LENGTHS_ORDERED
            and all(item["replications"] == module.BOOTSTRAP_REPLICATIONS for item in blocks)
            and all(
                item["validation_seed"] == module.validation_seed(item["block_length"])
                for item in blocks
            )
            and sum(1 for item in blocks if item["role"] == "PRIMARY") == 1,
            f"blocks={[item['block_length'] for item in blocks]}",
        )
    )
    checks.append(
        _check(
            "SIGNED_REPLICATES_ARE_ADMITTED_AND_FINITE",
            all(
                item["negative_replicates"]
                + item["zero_replicates"]
                + item["positive_replicates"]
                == module.BOOTSTRAP_REPLICATIONS
                for item in blocks
            )
            and verification.observed_raw_sha256 == record["raw_material_sha256"],
            module.REPLICATE_SIGN_POLICY,
        )
    )


def _runtime_checks(
    module: Any, verification: Any, checks: list[tuple[str, bool, str]]
) -> None:
    sealed = synthetic_runtime_identity("A")
    same = synthetic_runtime_identity("A")
    drifted = synthetic_runtime_identity("B")
    equal_comparison = module.compare_runtime_identities(sealed, same)
    drift_comparison = module.compare_runtime_identities(sealed, drifted)
    checks.append(
        _check(
            "CLOSED_SCHEMA_RUNTIME_COMPARATOR",
            equal_comparison.conforming
            and equal_comparison.equal
            and drift_comparison.conforming
            and not drift_comparison.equal
            and drift_comparison.first_difference == "python.version_full",
            f"first_difference={drift_comparison.first_difference}",
        )
    )

    accepted = module.assess_c0(
        sealed_identity=sealed,
        pre_permit_identity=same,
        golden_binding_verification=verification,
    )
    refused = module.assess_c0(
        sealed_identity=sealed,
        pre_permit_identity=drifted,
        golden_binding_verification=verification,
    )
    boolean_only = module.assess_c0(
        sealed_identity=sealed, pre_permit_identity=same, golden_binding_verification=True
    )
    checks.append(
        _check(
            "PRE_START_EXECUTION_ASSESSMENT_IS_PURE_AND_GRANTS_NOTHING",
            not accepted.refused
            and refused.refused
            and boolean_only.refused
            and refused.terminal_class is None
            and refused.permits_consumed == 0
            and refused.fits_performed == 0
            and refused.validation_state == "UNOPENED"
            and not refused.witness_created,
            "a caller boolean cannot stand in for the ratified golden binding",
        )
    )


def _scoring_checkpoint_checks(
    module: Any, verification: Any, ledger: Any, checks: list[tuple[str, bool, str]]
) -> None:
    sealed = synthetic_runtime_identity("A")
    same = synthetic_runtime_identity("A")
    fits = ledger.fits_ordered
    seal_verification = module.verify_deployment_seals(fits)
    ready_but_refused = module.assess_c0v(
        sealed_c0_identity=sealed,
        sealed_c0v_identity=same,
        pre_witness_identity=same,
        golden_binding_verification=verification,
        sealed_fits=fits,
        seal_verification=seal_verification,
        untrusted_grant2_claim=None,
    )
    spoofed = module.assess_c0v(
        sealed_c0_identity=sealed,
        sealed_c0v_identity=same,
        pre_witness_identity=same,
        golden_binding_verification=verification,
        sealed_fits=fits,
        seal_verification=seal_verification,
        untrusted_grant2_claim={"claim": "synthetic"},
    )
    asserted_only = module.assess_c0v(
        sealed_c0_identity=sealed,
        sealed_c0v_identity=same,
        pre_witness_identity=same,
        golden_binding_verification=verification,
        sealed_fits=True,
        seal_verification=True,
        untrusted_grant2_claim=True,
    )
    checks.append(
        _check(
            "SCORING_READINESS_NEVER_MINTS_OR_AUTHENTICATES_OWNER_GRANT_2",
            ready_but_refused.refused
            and spoofed.refused
            and asserted_only.refused
            and ready_but_refused.refusal_reasons
            == (module.SEPARATE_OWNER_GRANT_2_REFUSAL,)
            and ready_but_refused.terminal_class is None
            and ready_but_refused.grant_id is None
            and not ready_but_refused.witness_created
            and not ready_but_refused.authorizes_refit
            and spoofed.grant_id is None,
            "verified seals are readiness only; Grant 2 is unavailable in this slice",
        )
    )


def _deployment_checks(module: Any, checks: list[tuple[str, bool, str]]) -> Any:
    deficient = module.run_ordered_deployment_fits(synthetic_rank_deficient_sample(module))
    mismatched = module.run_ordered_deployment_fits(
        synthetic_mismatched_identity_sample(module)
    )
    checks.append(
        _check(
            "RANK_AND_IDENTITY_GATES_PRECEDE_ANY_SOLVE",
            not deficient.precheck.may_fit
            and deficient.permits_consumed == 0
            and deficient.fits_attempted == 0
            and deficient.fits_ordered == ()
            and bool(deficient.structural_triggers)
            and not mismatched.precheck.may_fit
            and mismatched.permits_consumed == 0
            and mismatched.fits_attempted == 0
            and bool(mismatched.integrity_defects),
            "solves_attempted=0 for both refused synthetic samples",
        )
    )

    sample = synthetic_train_sample(module)
    ledger = module.run_ordered_deployment_fits(sample)
    if len(ledger.fits_ordered) != len(module.MODEL_ORDER):
        raise RunnerRefusal(
            "SELF_CHECK_FAILED", "both ordered synthetic model solves must succeed"
        )
    base_fit, har_fit = ledger.fits_ordered
    checks.append(
        _check(
            "ORDERED_BASE_THEN_HAR_SYNTHETIC_SOLVE_ACCOUNTING",
            ledger.fits_attempted == module.CONFIRMATORY_FIT_BUDGET
            and ledger.fits_succeeded == module.CONFIRMATORY_FIT_BUDGET
            and ledger.seals_verified == len(module.MODEL_ORDER)
            and ledger.terminal_class is None
            and ledger.validation_state == "UNOPENED"
            and tuple(item.model_id for item in ledger.fits_ordered) == module.MODEL_ORDER
            and base_fit.columns == module.MODEL_COLUMNS[base_fit.model_id]
            and har_fit.columns == module.MODEL_COLUMNS[har_fit.model_id],
            f"accounting_budget={ledger.budget_id}",
        )
    )
    checks.append(
        _check(
            "MODEL_LOCAL_DUAN_FACTORS_ARE_NEVER_SHARED",
            base_fit.duan_factor > 0.0
            and har_fit.duan_factor > 0.0
            and math.isfinite(base_fit.duan_factor)
            and math.isfinite(har_fit.duan_factor)
            and base_fit.duan_factor != har_fit.duan_factor
            and base_fit.row_identity_sha256 == har_fit.row_identity_sha256,
            module.DUAN_BASIS,
        )
    )
    return sample, ledger


def _metric_checks(
    module: Any, sample: Any, ledger: Any, checks: list[tuple[str, bool, str]]
) -> Any:
    base_fit, har_fit = ledger.fits_ordered
    forecast_base = module.deployment_forecast(
        base_fit, synthetic_scoring_design(module, base_fit.model_id, sample)
    )
    forecast_har = module.deployment_forecast(
        har_fit, synthetic_scoring_design(module, har_fit.model_id, sample)
    )
    actual = numpy.ascontiguousarray(numpy.exp(sample.log_target), dtype=numpy.float64)
    losses = module.compute_row_losses(actual, forecast_base, forecast_har)
    metrics = module.compute_decision_metrics(losses)
    checks.append(
        _check(
            "QLIKE_STORED_ORDER_LEFT_FOLD_METRICS",
            losses.row_count == len(sample.row_identities)
            and metrics.scored
            and metrics.mean_base > 0.0
            and metrics.mean_har >= 0.0
            and math.isfinite(metrics.mean_difference)
            and metrics.relative_qlike_reduction is not None,
            f"row_count={metrics.row_count}",
        )
    )

    identity_losses = module.compute_row_losses(actual, actual, actual)
    identity_metrics = module.compute_decision_metrics(identity_losses)
    checks.append(
        _check(
            "QLIKE_IDENTITY_FORECAST_IS_ZERO_LOSS",
            identity_metrics.mean_base == 0.0
            and identity_metrics.mean_har == 0.0
            and identity_metrics.mean_difference == 0.0,
            "a/f == 1 gives exactly zero loss",
        )
    )

    nonfinite = numpy.ascontiguousarray(
        numpy.full(actual.shape, numpy.inf), dtype=numpy.float64
    )
    refused_nonfinite = False
    try:
        module.compute_row_losses(actual, nonfinite, forecast_har)
    except module.Test3ConfirmatoryValidationError:
        refused_nonfinite = True
    checks.append(
        _check(
            "EVERY_AUTHORITATIVE_INTERMEDIATE_MUST_BE_FINITE",
            refused_nonfinite
            and math.isfinite(metrics.mean_base)
            and math.isfinite(metrics.mean_har)
            and math.isfinite(metrics.mean_difference)
            and math.isfinite(base_fit.condition_number),
            "nonfinite operands and nonfinite D are refused",
        )
    )
    return metrics


def _support_checks(module: Any, checks: list[tuple[str, bool, str]]) -> Any:
    supported_rows = synthetic_acf_rows(module, constant=False)
    supported = module.assess_within_session_acf(supported_rows)
    constant = module.assess_within_session_acf(synthetic_acf_rows(module, constant=True))
    interleaved = module.assess_within_session_acf(
        synthetic_acf_rows(module, constant=False, interleaved=True)
    )
    checks.append(
        _check(
            "EXACT_WITHIN_SESSION_ACF",
            not supported.integrity_defects
            and not supported.support_undefined_lags
            and len(supported.lags) == len(module.ACF_LAGS)
            and supported.design_effect is not None
            and supported.effective_sample_size is not None
            and not constant.integrity_defects
            and bool(constant.support_undefined_lags)
            and all(item.rho_observed is None for item in constant.lags)
            and bool(interleaved.integrity_defects),
            f"undefined_lags={constant.support_undefined_lags}",
        )
    )

    honest = module.build_validation_support(
        supported,
        declared_common_eligible_rows=supported.row_count,
        declared_unique_sessions=supported.unique_session_count,
    )
    overstated = module.build_validation_support(
        supported,
        declared_common_eligible_rows=supported.row_count,
        declared_unique_sessions=module.MINIMUM_VALIDATION_SESSIONS,
    )
    checks.append(
        _check(
            "DERIVED_SESSION_COUNT_GATE_IGNORES_CALLER_SCALARS",
            honest.derived_unique_sessions == len({row.session_id for row in supported_rows})
            and not honest.reconciliation_defects
            and bool(overstated.reconciliation_defects)
            and "FEWER_THAN_20_UNIQUE_CHRONOLOGICAL_VALIDATION_SESSIONS"
            in module.assess_validation_support(overstated),
            f"derived_sessions={honest.derived_unique_sessions}",
        )
    )
    return supported


def _classification_checks(
    module: Any, metrics: Any, supported: Any, checks: list[tuple[str, bool, str]]
) -> None:
    reconciled = module.ConfirmatoryCounters(
        fits_attempted=2,
        fits_succeeded=2,
        permits_consumed=2,
        seals_verified=2,
        validation_openings=1,
    )
    breached = module.ConfirmatoryCounters(
        fits_attempted=2,
        fits_succeeded=2,
        permits_consumed=2,
        seals_verified=2,
        validation_openings=1,
        final_test_requests=1,
    )
    checks.append(
        _check(
            "COUNTER_AND_BUDGET_RECONCILIATION",
            not module.reconcile_counters(reconciled)
            and "FINAL_TEST_REQUEST_COUNT_IS_NONZERO" in module.reconcile_counters(breached),
            "the final test remains sealed",
        )
    )

    support = module.build_validation_support(
        supported,
        declared_common_eligible_rows=supported.row_count,
        declared_unique_sessions=supported.unique_session_count,
    )
    scored_acf = module.assess_within_session_acf(
        synthetic_acf_rows(
            module,
            constant=False,
            sessions=module.MINIMUM_VALIDATION_SESSIONS,
        )
    )
    scored_support = module.build_validation_support(
        scored_acf,
        declared_common_eligible_rows=scored_acf.row_count,
        declared_unique_sessions=scored_acf.unique_session_count,
    )
    passing = module.evaluate_pass_criteria(metrics, 1.0, ())
    integrity_first = module.classify_confirmatory_terminal(
        integrity_defects=("SYNTHETIC_INTEGRITY_DEFECT",),
        validation_support=support,
        pass_assessment=passing,
    )
    structural = module.classify_confirmatory_terminal(
        deployment_precheck=module.precheck_deployment_designs(
            synthetic_rank_deficient_sample(module)
        ),
        pass_assessment=passing,
    )
    scored = module.classify_confirmatory_terminal(
        validation_support=scored_support, pass_assessment=passing
    )
    checks.append(
        _check(
            "INTEGRITY_BEFORE_SUPPORT_PRECEDENCE",
            integrity_first.terminal_class == module.TerminalClass.INVALID_EVIDENCE
            and integrity_first.tier == 1
            and structural.terminal_class == module.TerminalClass.UNDERPOWERED_STOP
            and structural.tier == 2
            and scored.terminal_class
            in (module.TerminalClass.CONFIRMED, module.TerminalClass.NOT_CONFIRMED),
            # Only the precedence tier is reported. No terminal-class token is
            # ever printed, so no line of this output can be read as a result.
            f"tiers={integrity_first.tier},{structural.tier},{scored.tier}",
        )
    )

    zero_difference = module.DecisionMetrics(
        row_count=1,
        mean_base=1.0,
        mean_har=1.0,
        mean_difference=0.0,
        relative_qlike_reduction=0.10,
        mean_base_hex=module.float_hex(1.0),
        mean_har_hex=module.float_hex(1.0),
        mean_difference_hex=module.float_hex(0.0),
        relative_qlike_reduction_hex=module.float_hex(0.10),
        scored=True,
        undefined_reasons=(),
    )
    boundary_zero_d = module.evaluate_pass_criteria(zero_difference, 1.0, ())
    boundary_zero_bound = module.evaluate_pass_criteria(metrics, 0.0, ())
    checks.append(
        _check(
            "ASYMMETRIC_EQUALITY_BOUNDARIES",
            not boundary_zero_d.passed
            and "D_STRICTLY_GREATER_THAN_ZERO" in boundary_zero_d.failures
            and "RELATIVE_QLIKE_REDUCTION_AT_LEAST_0.10" not in boundary_zero_d.failures
            and not boundary_zero_bound.passed
            and "PRIMARY_LOWER_BOUND_STRICTLY_GREATER_THAN_ZERO"
            in boundary_zero_bound.failures,
            "equality fails 1 and 3, equality passes 2",
        )
    )


def run_self_check(module: Any, binding_bytes: bytes) -> tuple[tuple[str, bool, str], ...]:
    """Exercise every pure surface once, on fixed synthetic operands only."""

    checks: list[tuple[str, bool, str]] = []
    verification = _golden_checks(module, binding_bytes, checks)
    _bootstrap_checks(module, verification, checks)
    _runtime_checks(module, verification, checks)
    sample, ledger = _deployment_checks(module, checks)
    _scoring_checkpoint_checks(module, verification, ledger, checks)
    metrics = _metric_checks(module, sample, ledger, checks)
    supported = _support_checks(module, checks)
    _classification_checks(module, metrics, supported, checks)
    return tuple(checks)


# --------------------------------------------------------------------------
# Entry point
# --------------------------------------------------------------------------


def main(argv: object = None) -> int:
    arguments = list(sys.argv[1:]) if argv is None else argv
    try:
        parse_arguments(arguments)
        require_hardened_startup()
        load_trusted_numpy()
        binding_bytes = read_ratified_binding_bytes()
        require_ratified_runtime_identity(binding_bytes)
        module = implementation_module()
        revalidate_numpy_snapshot()
        checks = run_self_check(module, binding_bytes)
        revalidate_numpy_snapshot()
    except RunnerRefusal as refusal:
        _emit(sys.stderr, f"{refusal.code}: {refusal.detail}")
        return 2
    except Exception as error:  # noqa: BLE001 - all unexpected failures map to stable output.
        _emit(sys.stderr, f"INTERNAL_NONCONFORMANCE: {type(error).__name__}")
        return 2

    for position, (name, passed, detail) in enumerate(checks, start=1):
        status = "PASS" if passed else "FAIL"
        _emit(sys.stdout, f"CHECK {position:02d} {name}: {status}: {detail}")
    failed = [name for name, passed, _detail in checks if not passed]
    if failed:
        _emit(sys.stderr, f"SELF_CHECK_FAILED: {','.join(failed)}")
        return 2
    _emit(
        sys.stdout,
        f"{SELF_CHECK_COMPLETE_TOKEN}: {CLASSIFICATION}: {LOCAL_RUNTIME_ORIGIN_DISPOSITION}",
    )
    _emit(sys.stdout, NO_CLAIM_TOKEN)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
