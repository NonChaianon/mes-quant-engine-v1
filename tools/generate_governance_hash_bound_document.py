"""Generate a governed Markdown document with a machine-computed hash-bound block.

An LLM (or any caller) supplies a hash-free UTF-8 template plus an ordered set of
LABEL -> repository-relative-path bindings.  This tool resolves every bound path under an
explicit repository root, reads its exact bytes, computes a lowercase SHA-256 digest and byte
count, and renders the complete Markdown hash block itself.  The caller never types, copies, or
repairs a digest: every hash-bearing byte in the final document is produced from the file
contents by this deterministic generator.

Security properties this module provides:

* The repository root itself is established with a single descriptor-rooted, ``O_NOFOLLOW``
  open of its own final path component, relative to its already-open, trusted parent directory,
  and its identity is bound immediately with ``fstat``.  That single open *is* the sole means of
  access: the returned root descriptor -- never a re-resolved pathname -- is used for every
  later read or write operation under the root.  The trusted parent descriptor and the root's
  own leaf name are separately retained, purely so that the root's name binding can be
  re-verified, by ``fstat`` identity comparison only (never by substituting a re-resolved
  descriptor for the retained root descriptor), both immediately before and immediately after
  publication.  This closes the gap left by validating the root at open time alone: a directory
  swapped in at the root's name after that open, but before or during publication, is turned
  into a stable, nonzero, governed ``REPOSITORY_ROOT_REPLACED`` error rather than a successful
  return value, even when complete, correctly hashed bytes happen to exist under the retained
  root descriptor.  A repository root with no distinct final path component to protect (for
  example ``/``, ``.``, or ``..``) has nothing further this re-verification can check.
* Descriptor-rooted, ``O_NOFOLLOW`` traversal for every bound input path.  Every path segment
  below the root is opened relative to its immediate parent descriptor (never re-resolved from
  a path string), so a directory or leaf swapped in after a segment has already been opened
  cannot redirect that segment's resolution.  The final regular-file descriptor is retained and
  hashed directly from that descriptor, and a before/after ``fstat`` comparison detects a file
  that was observed to mutate while it was being read.
* The same descriptor-relative discipline applies to the output side: the output parent
  directory is opened once as a descriptor and every subsequent operation (temporary-file
  creation, unlink, fsync, the publishing ``fclonefileat`` clone, directory fsync) is performed
  relative to that single retained descriptor.  The pathname that names that parent directory is
  independently re-resolved and compared, by ``fstat`` identity, against the retained descriptor both
  immediately before and immediately after publication.  A success return value or CLI stdout
  line names the requested pathname only when its root and parent bindings matched the retained
  descriptors at that final observation; POSIX offers no guarantee that a pathname keeps naming
  the same directory forever, so this module makes no claim about, and performs no check after,
  whatever may happen to that name once its own final observation has already reported success.
* The rendered document is published with a single Darwin fd-source atomic clone. A randomly
  named, mode-0600 temporary regular file is created directly under the retained output-parent
  descriptor with ``O_CREAT | O_EXCL | O_NOFOLLOW`` (refusing to follow or overwrite anything
  already at that name), and its name is unlinked from the output-parent directory's own listing
  *immediately*, before a single content byte is written, while the descriptor itself is
  retained. From that moment on the temporary bytes are reachable only through the retained
  descriptor -- never through any name a concurrent lister of the output-parent directory could
  observe. The complete rendered bytes are then written to that retained, nameless descriptor and
  fsynced. Publication is a single call to ``fclonefileat(src_fd, dst_dir_fd, dst_name, 0)`` --
  resolved once, at import-adjacent capability-check time, from the C runtime via ``ctypes`` with
  ``use_errno=True`` -- where ``src_fd`` is that same retained, nameless descriptor (never a
  re-resolved pathname) and ``dst_dir_fd``/``dst_name`` are the retained output-parent descriptor
  and validated final name. ``fclonefileat`` clones by descriptor identity, not by re-walking a
  pathname, so nothing an adversary can do to any *name* -- including recreating a file at the
  now-unlinked temporary name -- can redirect the clone's source. The kernel fails the call with
  ``EEXIST`` if the destination name already exists, so no separate existence check and no
  overwrite is possible; that ``EEXIST`` is mapped to the stable ``OUTPUT_PATH_EXISTS`` code
  (or ``OUTPUT_PATH_IS_SYMLINK`` when the colliding name is itself a symlink). There is no
  same-directory named-link fallback of any kind: a platform, symbol, or volume that cannot
  provide a working ``fclonefileat`` fails closed with a stable governed code instead of falling
  back to a weaker publication primitive. Only after the clone has succeeded is the temporary
  descriptor closed and the output-parent directory fsynced; a failure at either of those two
  final steps is reported as a stable, nonzero, governed error, and this module never attempts to
  roll back an already-published file, because doing so cannot be done safely once the clone is
  durable.
* Templates must place the single generator placeholder on its own complete line and must not
  already contain the generator's own BEGIN/END control markers.  Templates are also rejected
  if they contain a hand-transcribed or lightly obfuscated SHA-256-shaped digest: a contiguous
  64-character hex run, a hex run split only by ASCII whitespace/newlines, a hex run split only
  by Unicode "format" (Cf) or zero-width characters, or a hex run split only by common
  Markdown/HTML separator punctuation.  This is a bounded, named set of concrete obfuscation
  classes; it is not a claim that arbitrary semantic re-encoding of a digest is detectable.
* Every governed rejection (argument parsing, stdin decoding, filesystem, write/sync/clone/
  unlink) is surfaced as a stable machine-readable code with a fixed, host-independent message
  shape (an ``errno`` number may be included; raw OS ``strerror`` text is never echoed).  No
  traceback is shown to the caller for a governed rejection.
"""

from __future__ import annotations

import argparse
import ctypes
import errno
import hashlib
import os
import re
import secrets
import stat
import sys
import unicodedata
from collections.abc import Sequence
from dataclasses import dataclass
from pathlib import Path, PurePosixPath

PLACEHOLDER = "<!-- GOVERNANCE_HASH_BLOCK_PLACEHOLDER -->"
HASH_BLOCK_BEGIN = "<!-- BEGIN GOVERNANCE_HASH_BLOCK -->"
HASH_BLOCK_END = "<!-- END GOVERNANCE_HASH_BLOCK -->"

_LABEL_RE = re.compile(r"^[A-Z][A-Z0-9_]{0,63}$")
_PATH_SEGMENT_RE = re.compile(r"^[A-Za-z0-9._-]+$")

_READ_CHUNK_BYTES = 1024 * 1024
_MIN_DIGEST_HEX_CHARS = 64

_HEX_DIGIT_SET = frozenset("0123456789abcdefABCDEF")
_WHITESPACE_SEPARATOR_CHARS = frozenset(" \t\r\n\f\v")
_MARKUP_SEPARATOR_CHARS = frozenset("`*_~|,.;<>/-")

_REQUIRED_OPEN_FLAG_NAMES = ("O_DIRECTORY", "O_NOFOLLOW", "O_RDONLY", "O_RDWR", "O_CREAT", "O_EXCL")

# Captured once, at import time, before any caller (including a test) can monkeypatch
# ``os.open``/``os.unlink`` with a wrapper.  The capability gate below asks whether *this
# platform's real* descriptor-relative primitives are present in the live, mutable
# ``os.supports_dir_fd`` capability set; it must never ask whether whatever object currently
# happens to be bound to one of these names (which a wrapper may have replaced for unrelated
# interception reasons) is a member of that set. Using the frozen, import-time identities keeps
# the gate a true platform-capability fact rather than an accidental function-identity check.
# Publication no longer uses ``os.link``/``os.mkdir``/``os.rmdir`` at all: the temporary
# publication file is created and unlinked (both ``dir_fd``-relative) directly under the
# output-parent descriptor, and the final name is produced by a single ``fclonefileat`` call
# (gated separately by ``_require_fclonefileat_capability``), never by a directory-based
# hard-link scheme.
_DIR_FD_REQUIRED_OS_FUNCTIONS = (os.open, os.unlink)

# A fixed, host-independent detail string for an invalid-UTF-8 template. This is a literal
# constant, never derived from ``UnicodeDecodeError.__str__`` (whose wording/position rendering
# is not a value this module treats as stable across platforms or Python versions), so the
# governed rejection detail is identical on every host and every invocation.
_TEMPLATE_NOT_UTF8_DETAIL = "template stdin is not valid UTF-8"


class GovernanceHashBoundDocumentError(RuntimeError):
    """A stable, fail-closed rejection with a machine-stable reason code."""

    def __init__(self, code: str, detail: str) -> None:
        super().__init__(f"{code}: {detail}")
        self.code = code
        self.detail = detail


@dataclass(frozen=True)
class _RepositoryRootHandle:
    """The retained descriptors and identity needed to detect a root-level name swap.

    ``root_fd`` is the sole descriptor used for every real filesystem operation under the
    repository root; it is never replaced or re-resolved after ``_open_repository_root_fd``
    returns. ``parent_fd`` is the trusted, already-open descriptor of the root's own parent
    directory, and ``leaf_name`` is the root's own final path component -- both retained solely
    so that ``_verify_root_binding_unchanged`` can reopen that same leaf name, fresh, relative to
    ``parent_fd`` and compare its identity by ``fstat`` against ``identity`` (the ``(st_dev,
    st_ino)`` pair captured when ``root_fd`` was first opened). That comparison never substitutes
    the freshly reopened descriptor for ``root_fd`` itself; it exists purely to detect, not to
    access. When the repository root has no distinct final path component to protect (for
    example ``/``, ``.``, or ``..``), ``parent_fd`` and ``leaf_name`` are ``None`` and no
    root-level name swap can be represented or detected, mirroring the documented limitation of
    ``_open_repository_root_fd`` for that case.
    """

    root_fd: int
    parent_fd: int | None
    leaf_name: str | None
    identity: tuple[int, int]


@dataclass(frozen=True)
class Binding:
    """One ordered LABEL -> repository-relative-path input binding."""

    label: str
    relative_path: str


# ---------------------------------------------------------------------------
# Governed descriptor close handling
# ---------------------------------------------------------------------------
#
# Every ``os.close`` call in this module is routed through exactly one of the two helpers below.
# The precedence between a close failure and any other error is decided at each call site, by
# construction, rather than by inspecting interpreter state: a call site either (a) is reached
# only while no other error is in flight, in which case a close failure is itself the sole
# reportable event and is converted into a stable governed error instead of an unguarded
# ``OSError``/traceback, or (b) is reached only as best-effort cleanup while a primary error (a
# ``GovernanceHashBoundDocumentError`` already constructed, or an exception already propagating)
# is in flight, in which case a close failure is swallowed so it can never replace, chain over, or
# otherwise mask that primary error.


def _close_best_effort(fd: int) -> None:
    """Close ``fd`` and unconditionally discard any failure.

    Reserved for call sites reached only while a primary error is already being constructed or is
    already propagating: a close failure here must never become the caller-visible error.
    """

    try:
        os.close(fd)
    except OSError:
        pass


def _close_or_raise(fd: int, *, code: str, detail: str) -> None:
    """Close ``fd`` and convert a failure into a stable governed error.

    Reserved for call sites reached only on an otherwise-successful path, where no other error is
    already in flight: a close failure here is the sole reportable event.
    """

    try:
        os.close(fd)
    except OSError as exc:
        raise GovernanceHashBoundDocumentError(code, f"{detail} (errno={exc.errno})") from exc


def _close_all_best_effort(fds: Sequence[int]) -> None:
    for fd in fds:
        _close_best_effort(fd)


def _close_all_or_raise(fds: Sequence[int], *, code: str, detail: str) -> None:
    """Close every fd in ``fds``, then raise once for the first failure, if any.

    Every descriptor is attempted regardless of an earlier failure among them (no descriptor is
    skipped/leaked just because an earlier one could not be closed); only the first failure is
    reported, as a stable governed error, once every close attempt has been made.
    """

    first_error: OSError | None = None
    for fd in fds:
        try:
            os.close(fd)
        except OSError as exc:
            if first_error is None:
                first_error = exc
    if first_error is not None:
        raise GovernanceHashBoundDocumentError(
            code, f"{detail} (errno={first_error.errno})"
        ) from first_error


# ---------------------------------------------------------------------------
# Capability gate
# ---------------------------------------------------------------------------


def _require_descriptor_relative_capability() -> None:
    """Fail closed if this platform lacks the primitives this module relies on."""

    if any(not hasattr(os, name) for name in _REQUIRED_OPEN_FLAG_NAMES):
        raise GovernanceHashBoundDocumentError(
            "CAPABILITY_DIR_FD_UNSUPPORTED",
            "this platform does not expose the POSIX open flags required for "
            "descriptor-relative traversal",
        )
    if any(func not in os.supports_dir_fd for func in _DIR_FD_REQUIRED_OS_FUNCTIONS):
        raise GovernanceHashBoundDocumentError(
            "CAPABILITY_DIR_FD_UNSUPPORTED",
            "this platform does not support descriptor-relative (dir_fd) filesystem "
            "operations for every primitive this tool requires",
        )


# ---------------------------------------------------------------------------
# fclonefileat binding (Darwin fd-source atomic publication primitive)
# ---------------------------------------------------------------------------
#
# ``fclonefileat`` is resolved lazily, once, and cached: the first successful resolution is
# reused for the lifetime of the process, and a resolution failure is never cached (so a test
# that monkeypatches this function back to the real resolver, or a process running against a
# genuinely different platform state, is never stuck with a stale negative result). There is no
# named-link or any other fallback publication primitive: a platform, symbol, or C-runtime-load
# failure here is a stable, nonzero, governed rejection, never a silent downgrade to a weaker
# publication scheme.

_fclonefileat_cache: dict[str, object] = {}


def _resolve_fclonefileat():  # type: ignore[no-untyped-def]
    """Resolve and cache the ``fclonefileat(int, int, const char *, int) -> int`` C binding.

    ``fclonefileat`` is a Darwin-only primitive; this module makes no attempt to run on a
    platform that lacks it, and never falls back to a named-link or copy-based publication
    scheme when it is unavailable. The C runtime is loaded once via ``ctypes.CDLL(None,
    use_errno=True)`` -- the default, global process namespace, which already contains
    ``libSystem`` on every live Python process on Darwin -- and the symbol is looked up and
    given fixed C argument/return types exactly once. Every governed rejection this function can
    raise is the single, stable ``CAPABILITY_FCLONEFILEAT_UNSUPPORTED`` code: this function
    reports *whether a working binding exists at all*, never a per-call outcome (per-call
    ``fclonefileat`` outcomes, including ``EEXIST``/``ENOTSUP``/``EXDEV``/other errno values, are
    handled separately by ``_invoke_fclonefileat`` and its caller).
    """

    cached = _fclonefileat_cache.get("func")
    if cached is not None:
        return cached
    if sys.platform != "darwin":
        raise GovernanceHashBoundDocumentError(
            "CAPABILITY_FCLONEFILEAT_UNSUPPORTED",
            "this platform is not Darwin and does not provide fclonefileat; there is no "
            "named-link or other publication fallback",
        )
    try:
        libc = ctypes.CDLL(None, use_errno=True)
    except OSError as exc:
        raise GovernanceHashBoundDocumentError(
            "CAPABILITY_FCLONEFILEAT_UNSUPPORTED",
            "the C runtime library providing fclonefileat could not be loaded",
        ) from exc
    try:
        func = libc.fclonefileat
    except AttributeError as exc:
        raise GovernanceHashBoundDocumentError(
            "CAPABILITY_FCLONEFILEAT_UNSUPPORTED",
            "the C runtime library does not export fclonefileat",
        ) from exc
    func.argtypes = (ctypes.c_int, ctypes.c_int, ctypes.c_char_p, ctypes.c_int)
    func.restype = ctypes.c_int
    _fclonefileat_cache["func"] = func
    return func


def _require_fclonefileat_capability() -> None:
    """Fail closed, before any input is read, if ``fclonefileat`` is not usable on this host."""

    _resolve_fclonefileat()


def _invoke_fclonefileat(src_fd: int, dst_dir_fd: int, dst_name: str) -> None:
    """Call ``fclonefileat(src_fd, dst_dir_fd, dst_name, 0)``, raising ``OSError`` on failure.

    ``src_fd`` must be the retained descriptor of the already-written, already-fsynced,
    already-unlinked temporary publication file: the clone is resolved by descriptor identity,
    never by re-walking any pathname, so nothing that happens to any *name* -- including a name
    an adversary recreates at the temporary file's now-unlinked former name -- can redirect the
    clone's source. ``flags`` is always ``0``: this module never requests or relies on an
    overwrite-capable clone mode, so the destination name must not already exist, and the kernel
    itself enforces that by failing with ``EEXIST`` rather than this module performing a
    separate, racy existence check beforehand.
    """

    func = _resolve_fclonefileat()
    ctypes.set_errno(0)
    result = func(src_fd, dst_dir_fd, dst_name.encode("utf-8"), 0)
    if result != 0:
        err = ctypes.get_errno()
        raise OSError(err, os.strerror(err))


# ---------------------------------------------------------------------------
# Repository root
# ---------------------------------------------------------------------------


def _repository_root_display_path(repository_root: Path) -> Path:
    """An absolute path used only to build informational return values.

    This is never used to open, reopen, or otherwise access the filesystem; the ``root_fd`` on the
    handle returned by ``_open_repository_root_fd`` is the sole descriptor used for every real
    operation under the root.
    """

    candidate = Path(repository_root)
    if candidate.is_absolute():
        return candidate
    return Path.cwd() / candidate


def _open_repository_root_fd(repository_root: Path) -> _RepositoryRootHandle:
    """Open the repository root exactly once as a directory descriptor and bind its identity.

    The previous implementation validated the repository root by resolving and stat'ing it as a
    pathname (``Path.resolve(strict=True)`` plus ``is_dir()``) and then, in a wholly separate
    step, reopened that same pathname string with ``os.open``. Between those two steps, an
    attacker able to replace the directory named by that pathname (for example by renaming it
    aside and creating a fresh directory, or a symlink, in its place) could redirect every
    subsequent bound-input and output operation into the replacement -- a classic
    checked-then-reopen TOCTOU.

    This function closes the access-time half of that gap. The repository root's parent chain is
    treated as the trusted filesystem anchor and is resolved by the operating system exactly
    once, the ordinary way, since it is supplied by the trusted caller and is not the part of the
    path this module must protect from a concurrent race. The repository root's own final path
    component -- the one name whose target this module must not let drift after it has been
    named -- is then opened relative to that already-open parent descriptor with
    ``O_DIRECTORY | O_NOFOLLOW``: a symlink swapped in at that name is refused rather than
    followed, and this open *is* the sole access-granting step; the returned descriptor -- never
    a re-resolved pathname -- is used for every later read or write operation under the root.

    The trusted parent descriptor and the root's own leaf name are not discarded once the root
    descriptor has been obtained: they are retained on the returned handle, alongside the
    ``(st_dev, st_ino)`` identity bound immediately with ``fstat``, purely so that the caller can
    later re-verify -- by a fresh, independent, descriptor-relative reopen compared only by
    ``fstat`` identity, never by substituting that fresh descriptor for the retained root
    descriptor -- that the root's name still identifies the same directory immediately before and
    immediately after publication. A root with no distinct final path component to protect (for
    example ``/``, ``.``, or ``..``) has no retained parent/leaf pair, since there is nothing
    below it this function could anchor a re-verification on.
    """

    candidate = Path(repository_root)
    raw = os.fspath(candidate)
    if raw == "":
        raise GovernanceHashBoundDocumentError(
            "REPOSITORY_ROOT_INVALID", "repository root is empty"
        )

    parent = candidate.parent
    leaf = candidate.name

    retained_parent_fd: int | None = None
    retained_leaf_name: str | None = None

    if leaf in ("", ".", ".."):
        # No distinct final path component exists to protect against a name-level swap (for
        # example the repository root is "/", ".", or "..", or a bare path that collapses to one
        # of those). Open it directly; there is nothing below it that this function could
        # instead anchor on, and no retained parent/leaf pair is produced.
        try:
            fd = os.open(raw, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW)
        except FileNotFoundError as exc:
            raise GovernanceHashBoundDocumentError(
                "REPOSITORY_ROOT_INVALID", f"repository root does not exist: {repository_root}"
            ) from exc
        except NotADirectoryError as exc:
            raise GovernanceHashBoundDocumentError(
                "REPOSITORY_ROOT_INVALID",
                f"repository root is not a directory: {repository_root}",
            ) from exc
        except OSError as exc:
            if exc.errno == errno.ELOOP:
                raise GovernanceHashBoundDocumentError(
                    "REPOSITORY_ROOT_INVALID", f"repository root is a symlink: {repository_root}"
                ) from exc
            raise GovernanceHashBoundDocumentError(
                "REPOSITORY_ROOT_NOT_OPENABLE",
                f"repository root could not be opened as a directory (errno={exc.errno})",
            ) from exc
    else:
        try:
            parent_fd = os.open(os.fspath(parent), os.O_RDONLY | os.O_DIRECTORY)
        except OSError as exc:
            raise GovernanceHashBoundDocumentError(
                "REPOSITORY_ROOT_INVALID",
                f"repository root parent directory could not be opened: {repository_root}",
            ) from exc
        try:
            fd = os.open(
                leaf, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW, dir_fd=parent_fd
            )
        except FileNotFoundError as exc:
            _close_best_effort(parent_fd)
            raise GovernanceHashBoundDocumentError(
                "REPOSITORY_ROOT_INVALID",
                f"repository root does not exist: {repository_root}",
            ) from exc
        except NotADirectoryError as exc:
            _close_best_effort(parent_fd)
            raise GovernanceHashBoundDocumentError(
                "REPOSITORY_ROOT_INVALID",
                f"repository root is not a directory: {repository_root}",
            ) from exc
        except OSError as exc:
            _close_best_effort(parent_fd)
            if exc.errno == errno.ELOOP:
                raise GovernanceHashBoundDocumentError(
                    "REPOSITORY_ROOT_INVALID",
                    f"repository root is a symlink: {repository_root}",
                ) from exc
            raise GovernanceHashBoundDocumentError(
                "REPOSITORY_ROOT_NOT_OPENABLE",
                f"repository root could not be opened as a directory (errno={exc.errno})",
            ) from exc
        else:
            # The trusted parent descriptor is retained (never closed here) precisely so that
            # the root's own leaf name can later be re-verified against it; closing it
            # immediately, as an earlier revision of this function did, would discard the one
            # trusted anchor a later re-verification needs.
            retained_parent_fd = parent_fd
            retained_leaf_name = leaf

    try:
        root_stat = os.fstat(fd)
    except OSError as exc:
        _close_best_effort(fd)
        if retained_parent_fd is not None:
            _close_best_effort(retained_parent_fd)
        raise GovernanceHashBoundDocumentError(
            "REPOSITORY_ROOT_NOT_OPENABLE",
            f"repository root could not be stat'd (errno={exc.errno})",
        ) from exc
    if not stat.S_ISDIR(root_stat.st_mode):
        _close_best_effort(fd)
        if retained_parent_fd is not None:
            _close_best_effort(retained_parent_fd)
        raise GovernanceHashBoundDocumentError(
            "REPOSITORY_ROOT_INVALID", f"repository root is not a directory: {repository_root}"
        )
    return _RepositoryRootHandle(
        root_fd=fd,
        parent_fd=retained_parent_fd,
        leaf_name=retained_leaf_name,
        identity=(root_stat.st_dev, root_stat.st_ino),
    )


# ---------------------------------------------------------------------------
# Path syntax validation (string-level; no filesystem access)
# ---------------------------------------------------------------------------


def _validate_relative_posix_path(
    value: str, *, malformed_code: str, outside_root_code: str
) -> PurePosixPath:
    if not isinstance(value, str) or value == "":
        raise GovernanceHashBoundDocumentError(malformed_code, f"path is empty: {value!r}")
    if "\x00" in value:
        raise GovernanceHashBoundDocumentError(malformed_code, "path contains a NUL byte")
    if "\\" in value or value.startswith(("/", "~")):
        raise GovernanceHashBoundDocumentError(
            malformed_code, f"path is not a POSIX-relative path: {value!r}"
        )
    segments = value.split("/")
    for segment in segments:
        if segment == "..":
            raise GovernanceHashBoundDocumentError(
                outside_root_code, f"path attempts to escape the repository root: {value!r}"
            )
        if segment in ("", "."):
            raise GovernanceHashBoundDocumentError(
                malformed_code, f"path has an unsafe segment: {value!r}"
            )
        if not _PATH_SEGMENT_RE.fullmatch(segment):
            raise GovernanceHashBoundDocumentError(
                malformed_code, f"path has an unsafe segment: {segment!r}"
            )
    return PurePosixPath(value)


def _validate_binding_labels_and_paths(bindings: Sequence[Binding]) -> list[Binding]:
    if not bindings:
        raise GovernanceHashBoundDocumentError(
            "BINDINGS_EMPTY", "at least one LABEL=RELATIVE_PATH binding is required"
        )
    seen_labels: set[str] = set()
    seen_paths: set[str] = set()
    normalized: list[Binding] = []
    for binding in bindings:
        if not _LABEL_RE.fullmatch(binding.label):
            raise GovernanceHashBoundDocumentError(
                "BINDING_LABEL_INVALID", f"label is invalid: {binding.label!r}"
            )
        if binding.label in seen_labels:
            raise GovernanceHashBoundDocumentError(
                "BINDING_LABEL_DUPLICATE", f"duplicate label: {binding.label!r}"
            )
        seen_labels.add(binding.label)

        normalized_path = _validate_relative_posix_path(
            binding.relative_path,
            malformed_code="BINDING_PATH_MALFORMED",
            outside_root_code="BINDING_PATH_OUTSIDE_ROOT",
        )
        normalized_text = normalized_path.as_posix()
        if normalized_text in seen_paths:
            raise GovernanceHashBoundDocumentError(
                "BINDING_PATH_DUPLICATE", f"duplicate path: {normalized_text!r}"
            )
        seen_paths.add(normalized_text)
        normalized.append(Binding(label=binding.label, relative_path=normalized_text))
    return normalized


# ---------------------------------------------------------------------------
# Descriptor-relative traversal
# ---------------------------------------------------------------------------


def _open_segment(current_fd: int, name: str, *, as_directory: bool) -> int:
    flags = os.O_RDONLY | os.O_NOFOLLOW
    if as_directory:
        flags |= os.O_DIRECTORY
    return os.open(name, flags, dir_fd=current_fd)


def _descend_to_file(root_fd: int, relative: PurePosixPath) -> int:
    """Open the final path component as a descriptor, race-free relative to ``root_fd``.

    Every intermediate directory is opened relative to the descriptor of its own immediate
    parent (never by re-resolving a path string), and every open uses ``O_NOFOLLOW`` so a
    symlink swapped in at any level is refused rather than followed.  The returned descriptor
    is owned by the caller.
    """

    parts = relative.parts
    display = relative.as_posix()
    current_fd = root_fd
    opened: list[int] = []
    try:
        for index, part in enumerate(parts):
            is_last = index == len(parts) - 1
            try:
                fd = _open_segment(current_fd, part, as_directory=not is_last)
            except FileNotFoundError as exc:
                raise GovernanceHashBoundDocumentError(
                    "BINDING_PATH_MISSING", f"path does not exist: {display!r}"
                ) from exc
            except NotADirectoryError as exc:
                raise GovernanceHashBoundDocumentError(
                    "BINDING_PATH_MISSING",
                    f"path component is not a directory: {display!r}",
                ) from exc
            except OSError as exc:
                if exc.errno == errno.ELOOP:
                    raise GovernanceHashBoundDocumentError(
                        "BINDING_PATH_IS_SYMLINK", f"path contains a symlink: {display!r}"
                    ) from exc
                raise GovernanceHashBoundDocumentError(
                    "BINDING_PATH_OPEN_FAILED",
                    f"path could not be opened (errno={exc.errno}): {display!r}",
                ) from exc
            current_fd = fd
            opened.append(fd)
    except GovernanceHashBoundDocumentError:
        _close_all_best_effort(opened)
        raise

    final_fd = opened.pop()
    _close_all_or_raise(
        opened,
        code="BINDING_PATH_INTERMEDIATE_CLOSE_FAILED",
        detail=(
            "an intermediate directory descriptor could not be closed while resolving: "
            f"{display!r}"
        ),
    )
    return final_fd


def _descend_to_output_parent(root_fd: int, relative: PurePosixPath) -> tuple[int, str, bool]:
    """Open the output's parent directory as a single retained descriptor.

    Returns ``(parent_fd, final_name, owns_parent_fd)``.  When the output path has no parent
    segments the output belongs directly to the repository root and ``parent_fd`` is ``root_fd``
    itself (``owns_parent_fd`` is ``False`` so the caller does not close it independently).
    """

    parts = relative.parts
    display = relative.as_posix()
    parent_parts = parts[:-1]
    final_name = parts[-1]
    current_fd = root_fd
    opened: list[int] = []
    try:
        for part in parent_parts:
            try:
                fd = _open_segment(current_fd, part, as_directory=True)
            except FileNotFoundError as exc:
                raise GovernanceHashBoundDocumentError(
                    "OUTPUT_PARENT_MISSING",
                    f"output parent directory does not exist: {display!r}",
                ) from exc
            except NotADirectoryError as exc:
                raise GovernanceHashBoundDocumentError(
                    "OUTPUT_PARENT_MISSING",
                    f"output parent path component is not a directory: {display!r}",
                ) from exc
            except OSError as exc:
                if exc.errno == errno.ELOOP:
                    raise GovernanceHashBoundDocumentError(
                        "OUTPUT_PARENT_UNSAFE",
                        f"output parent path contains a symlink: {display!r}",
                    ) from exc
                raise GovernanceHashBoundDocumentError(
                    "OUTPUT_PARENT_OPEN_FAILED",
                    f"output parent path could not be opened (errno={exc.errno}): {display!r}",
                ) from exc
            current_fd = fd
            opened.append(fd)
    except GovernanceHashBoundDocumentError:
        _close_all_best_effort(opened)
        raise

    if not opened:
        return root_fd, final_name, False

    parent_fd = opened.pop()
    _close_all_or_raise(
        opened,
        code="OUTPUT_PARENT_INTERMEDIATE_CLOSE_FAILED",
        detail=(
            "an intermediate output-parent directory descriptor could not be closed while "
            f"resolving: {display!r}"
        ),
    )
    return parent_fd, final_name, True


def _hash_fd_and_detect_mutation(fd: int, display: str) -> tuple[int, str]:
    try:
        initial = os.fstat(fd)
    except OSError as exc:
        raise GovernanceHashBoundDocumentError(
            "BINDING_PATH_OPEN_FAILED",
            f"could not stat bound input (errno={exc.errno}): {display!r}",
        ) from exc
    if stat.S_ISDIR(initial.st_mode):
        raise GovernanceHashBoundDocumentError(
            "BINDING_PATH_IS_DIRECTORY", f"path is a directory: {display!r}"
        )
    if not stat.S_ISREG(initial.st_mode):
        raise GovernanceHashBoundDocumentError(
            "BINDING_PATH_NOT_REGULAR_FILE", f"path is not a regular file: {display!r}"
        )

    digest = hashlib.sha256()
    size = 0
    try:
        while True:
            chunk = os.read(fd, _READ_CHUNK_BYTES)
            if not chunk:
                break
            digest.update(chunk)
            size += len(chunk)
    except OSError as exc:
        raise GovernanceHashBoundDocumentError(
            "BINDING_READ_FAILED",
            f"could not read bound input (errno={exc.errno}): {display!r}",
        ) from exc

    try:
        final = os.fstat(fd)
    except OSError as exc:
        raise GovernanceHashBoundDocumentError(
            "BINDING_PATH_OPEN_FAILED",
            f"could not re-stat bound input (errno={exc.errno}): {display!r}",
        ) from exc

    identity_before = (
        initial.st_dev,
        initial.st_ino,
        initial.st_size,
        initial.st_mtime_ns,
        initial.st_ctime_ns,
    )
    identity_after = (
        final.st_dev,
        final.st_ino,
        final.st_size,
        final.st_mtime_ns,
        final.st_ctime_ns,
    )
    if identity_before != identity_after:
        raise GovernanceHashBoundDocumentError(
            "BINDING_INPUT_MUTATED_DURING_READ",
            f"bound input changed while it was being read: {display!r}",
        )
    return size, digest.hexdigest()


# ---------------------------------------------------------------------------
# Rendered document assembly
# ---------------------------------------------------------------------------


def _build_hash_block(rows: Sequence[tuple[Binding, int, str]]) -> str:
    lines = [
        HASH_BLOCK_BEGIN,
        "| Label | Path | Bytes | SHA-256 |",
        "| --- | --- | --- | --- |",
    ]
    for binding, size, digest in rows:
        lines.append(f"| {binding.label} | `{binding.relative_path}` | {size} | `{digest}` |")
    lines.append(HASH_BLOCK_END)
    return "\n".join(lines)


def _classify_hex_run(count: int, whitespace: bool, fmt: bool, markup: bool) -> str | None:
    if count < _MIN_DIGEST_HEX_CHARS:
        return None
    if fmt:
        return "TEMPLATE_CONTAINS_FORMAT_CHARACTER_SPLIT_DIGEST"
    if markup:
        return "TEMPLATE_CONTAINS_MARKUP_SPLIT_DIGEST"
    if whitespace:
        return "TEMPLATE_CONTAINS_WHITESPACE_SPLIT_DIGEST"
    return "TEMPLATE_CONTAINS_RAW_SHA256"


def _find_digest_obfuscation_code(text: str) -> str | None:
    """Detect a bounded, named set of manual-digest obfuscation classes.

    This recognizes: a contiguous 64+ character hex run, the same run split only by ASCII
    whitespace/newlines, split only by Unicode "format" (category Cf, which includes the
    zero-width space/joiner family and the byte-order mark), or split only by common
    Markdown/HTML separator punctuation.  A separator only counts as "splitting" the run when
    it is sandwiched between two hex digits that belong to the same run; separators that merely
    precede or trail an otherwise-contiguous run (ordinary prose spacing/punctuation) do not.
    This is a bounded, named set of concrete classes; it does not and cannot claim to catch
    arbitrary semantic re-encoding of a digest.
    """

    hex_count = 0
    saw_whitespace = False
    saw_format = False
    saw_markup = False
    pending_whitespace = False
    pending_format = False
    pending_markup = False

    for ch in text:
        if ch in _HEX_DIGIT_SET:
            if hex_count > 0:
                if pending_format:
                    saw_format = True
                elif pending_markup:
                    saw_markup = True
                elif pending_whitespace:
                    saw_whitespace = True
            pending_whitespace = pending_format = pending_markup = False
            hex_count += 1
            continue

        is_format = unicodedata.category(ch) == "Cf"
        is_whitespace = ch in _WHITESPACE_SEPARATOR_CHARS
        is_markup = ch in _MARKUP_SEPARATOR_CHARS
        if is_format or is_whitespace or is_markup:
            if hex_count > 0:
                pending_format = pending_format or is_format
                pending_whitespace = pending_whitespace or is_whitespace
                pending_markup = pending_markup or is_markup
            continue

        code = _classify_hex_run(hex_count, saw_whitespace, saw_format, saw_markup)
        if code is not None:
            return code
        hex_count = 0
        saw_whitespace = saw_format = saw_markup = False
        pending_whitespace = pending_format = pending_markup = False

    return _classify_hex_run(hex_count, saw_whitespace, saw_format, saw_markup)


def _validate_template(template_text: str) -> None:
    if HASH_BLOCK_BEGIN in template_text or HASH_BLOCK_END in template_text:
        raise GovernanceHashBoundDocumentError(
            "TEMPLATE_CONTAINS_CONTROL_MARKER",
            "template already contains a generated hash-block control marker",
        )
    occurrences = template_text.count(PLACEHOLDER)
    if occurrences != 1:
        raise GovernanceHashBoundDocumentError(
            "TEMPLATE_PLACEHOLDER_COUNT_INVALID",
            f"expected exactly one complete-block placeholder, found {occurrences}",
        )
    if sum(1 for line in template_text.split("\n") if line == PLACEHOLDER) != 1:
        raise GovernanceHashBoundDocumentError(
            "TEMPLATE_PLACEHOLDER_NOT_OWN_LINE",
            "the placeholder must appear as its own complete line with no other content",
        )
    obfuscation_code = _find_digest_obfuscation_code(template_text)
    if obfuscation_code is not None:
        raise GovernanceHashBoundDocumentError(
            obfuscation_code,
            "template contains a manually transcribed or obfuscated SHA-256-shaped digest",
        )


def _decode_utf8_template(data: bytes) -> str:
    try:
        return data.decode("utf-8")
    except UnicodeDecodeError as exc:
        # ``exc`` (and ``str(exc)``) is never echoed: ``UnicodeDecodeError.__str__`` embeds a
        # codec name and a byte-offset/reason rendering that this module does not treat as a
        # stable value across platforms or Python versions. The detail is instead the fixed,
        # host-independent literal ``_TEMPLATE_NOT_UTF8_DETAIL``; ``exc`` is chained only as the
        # machine-readable ``__cause__`` for programmatic introspection, never surfaced to a CLI
        # caller.
        raise GovernanceHashBoundDocumentError(
            "TEMPLATE_NOT_UTF8", _TEMPLATE_NOT_UTF8_DETAIL
        ) from exc


# ---------------------------------------------------------------------------
# Atomic, no-overwrite publication
# ---------------------------------------------------------------------------


def _write_all(fd: int, data: bytes) -> None:
    view = memoryview(data)
    length = len(view)
    offset = 0
    while offset < length:
        offset += os.write(fd, view[offset:])


_TEMP_FILE_SUFFIX = ".mestmp"

_FCLONEFILEAT_UNSUPPORTED_ERRNOS = frozenset(
    {
        errno.ENOTSUP,
        getattr(errno, "EOPNOTSUPP", errno.ENOTSUP),
        errno.ENOSYS,
    }
)


def _random_temp_name() -> str:
    return f".{secrets.token_hex(16)}{_TEMP_FILE_SUFFIX}"


def _atomic_publish(parent_fd: int, final_name: str, data: bytes) -> None:
    """Publish ``data`` under ``final_name`` inside ``parent_fd`` without ever overwriting.

    Sequence: create a randomly named, mode-0600 regular file directly under ``parent_fd`` with
    ``O_CREAT | O_EXCL | O_NOFOLLOW``; unlink that name from ``parent_fd``'s own listing
    *immediately*, before a single content byte is written, while retaining the descriptor --
    from this point on the not-yet-published bytes are reachable only through the retained,
    nameless descriptor, never through any name a concurrent lister of the output-parent
    directory could observe; write the complete rendered bytes to that descriptor and fsync it;
    then publish with a single atomic, non-overwriting ``fclonefileat`` call whose source is the
    retained, nameless descriptor (never a re-resolved pathname) and whose destination is
    resolved through the retained output-parent descriptor and the validated final name. There is
    no same-directory named-link or other fallback: an unusable ``fclonefileat`` binding, an
    unsupported volume, or any other clone failure is a stable, nonzero, governed rejection.
    Once the clone has succeeded the document is durably visible under its final name; every
    failure after that point (temporary-descriptor close, parent-directory fsync) is reported as
    a stable governed error without attempting to roll back the already-published file.
    """

    temp_name = _random_temp_name()
    try:
        temp_fd = os.open(
            temp_name,
            os.O_RDWR | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW,
            0o600,
            dir_fd=parent_fd,
        )
    except OSError as exc:
        raise GovernanceHashBoundDocumentError(
            "OUTPUT_TEMP_CREATE_FAILED",
            f"could not create the private temporary output file (errno={exc.errno})",
        ) from exc

    try:
        os.unlink(temp_name, dir_fd=parent_fd)
    except OSError as exc:
        _close_best_effort(temp_fd)
        raise GovernanceHashBoundDocumentError(
            "OUTPUT_TEMP_UNLINK_FAILED",
            "could not unlink the private temporary output file's own name before writing "
            f"(errno={exc.errno})",
        ) from exc

    try:
        _write_all(temp_fd, data)
    except OSError as exc:
        _close_best_effort(temp_fd)
        raise GovernanceHashBoundDocumentError(
            "OUTPUT_TEMP_WRITE_FAILED",
            f"could not write the private temporary output file (errno={exc.errno})",
        ) from exc

    try:
        os.fsync(temp_fd)
    except OSError as exc:
        _close_best_effort(temp_fd)
        raise GovernanceHashBoundDocumentError(
            "OUTPUT_TEMP_FSYNC_FAILED",
            f"could not durably flush the private temporary output file (errno={exc.errno})",
        ) from exc

    try:
        _invoke_fclonefileat(temp_fd, parent_fd, final_name)
    except GovernanceHashBoundDocumentError:
        _close_best_effort(temp_fd)
        raise
    except OSError as exc:
        _close_best_effort(temp_fd)
        err = exc.errno
        if err == errno.EEXIST:
            code = "OUTPUT_PATH_EXISTS"
            try:
                existing = os.stat(final_name, dir_fd=parent_fd, follow_symlinks=False)
                if stat.S_ISLNK(existing.st_mode):
                    code = "OUTPUT_PATH_IS_SYMLINK"
            except (OSError, ValueError, NotImplementedError):
                pass
            raise GovernanceHashBoundDocumentError(
                code, "output path already exists and the governed document was not written"
            ) from exc
        if err in _FCLONEFILEAT_UNSUPPORTED_ERRNOS:
            raise GovernanceHashBoundDocumentError(
                "OUTPUT_FCLONEFILEAT_UNSUPPORTED",
                "the output volume or filesystem does not support fclonefileat cloning "
                f"(errno={err}); no named-link or other fallback was attempted",
            ) from exc
        if err == errno.EXDEV:
            raise GovernanceHashBoundDocumentError(
                "OUTPUT_FCLONEFILEAT_CROSS_DEVICE",
                f"fclonefileat cannot clone across devices/volumes (errno={err})",
            ) from exc
        raise GovernanceHashBoundDocumentError(
            "OUTPUT_FCLONEFILEAT_FAILED",
            f"could not publish the output file via fclonefileat (errno={err})",
        ) from exc

    # The document is now durably visible under its final name via the atomic clone above.
    # Everything from here on is cleanup/durability confirmation; a failure here must never be
    # treated as license to remove or otherwise roll back the already-published file.
    _close_or_raise(
        temp_fd,
        code="OUTPUT_TEMP_CLOSE_FAILED",
        detail=(
            "the output file is published but its temporary file descriptor could not be "
            "closed; no rollback was attempted"
        ),
    )

    try:
        os.fsync(parent_fd)
    except OSError as exc:
        raise GovernanceHashBoundDocumentError(
            "OUTPUT_DIRECTORY_FSYNC_FAILED",
            "the output file is published but its directory durability could not be confirmed "
            f"(errno={exc.errno}); no rollback was attempted",
        ) from exc


# ---------------------------------------------------------------------------
# Output parent / repository root identity re-verification
# ---------------------------------------------------------------------------


def _fd_identity(fd: int, *, stage: str, code: str, subject: str) -> tuple[int, int]:
    try:
        st = os.fstat(fd)
    except OSError as exc:
        raise GovernanceHashBoundDocumentError(
            code,
            f"{subject} identity could not be re-verified {stage} publication "
            f"(errno={exc.errno})",
        ) from exc
    return st.st_dev, st.st_ino


def _verify_output_parent_binding_unchanged(
    root_fd: int, relative: PurePosixPath, retained_parent_fd: int, *, stage: str
) -> None:
    """Fail closed if the requested output path no longer names the retained parent descriptor.

    A fresh descriptor-relative resolution of the same parent path components is performed --
    with the identical O_NOFOLLOW, descriptor-relative discipline used to obtain
    ``retained_parent_fd`` in the first place -- purely to compare identity by ``fstat``; the
    freshly opened descriptor is discarded immediately afterward and is never substituted for the
    retained one, so every actual read or write always goes through ``retained_parent_fd`` alone.
    Calling this both immediately before and immediately after publication means a success return
    value or CLI stdout line is produced only when this binding matched the retained descriptor
    at both of those observations -- whether the mismatching swap happened while the parent
    descriptor was idle or during the publish itself. This module makes no claim about, and
    performs no check after, whatever may happen to that name once the final observation has
    already reported success; POSIX offers no way to guarantee a pathname keeps naming the same
    directory beyond the moment it was last observed.
    """

    try:
        fresh_parent_fd, _ignored_final_name, fresh_owns = _descend_to_output_parent(
            root_fd, relative
        )
    except GovernanceHashBoundDocumentError as exc:
        raise GovernanceHashBoundDocumentError(
            "OUTPUT_PARENT_REPLACED",
            f"output parent directory binding could not be re-verified {stage} publication: "
            f"{exc.code}",
        ) from exc

    try:
        mismatch = _fd_identity(
            retained_parent_fd,
            stage=stage,
            code="OUTPUT_PARENT_REPLACED",
            subject="output parent directory",
        ) != _fd_identity(
            fresh_parent_fd,
            stage=stage,
            code="OUTPUT_PARENT_REPLACED",
            subject="output parent directory",
        )
    except BaseException:
        if fresh_owns:
            _close_best_effort(fresh_parent_fd)
        raise
    if fresh_owns:
        _close_or_raise(
            fresh_parent_fd,
            code="OUTPUT_PARENT_VERIFICATION_CLOSE_FAILED",
            detail=(
                "the freshly-resolved output parent verification descriptor could not be "
                f"closed {stage} publication"
            ),
        )

    if mismatch:
        if stage == "before":
            detail = (
                "output parent directory was replaced before publication; the governed "
                "document was not written"
            )
        else:
            detail = (
                "output parent directory was replaced during publication; the document is "
                "already published under its original directory identity but this call will "
                "not report a pathname that no longer identifies it, and no rollback was "
                "attempted"
            )
        raise GovernanceHashBoundDocumentError("OUTPUT_PARENT_REPLACED", detail)


def _verify_root_binding_unchanged(handle: _RepositoryRootHandle, *, stage: str) -> None:
    """Fail closed if the repository root's own name no longer identifies ``handle.root_fd``.

    When the repository root has no distinct final path component to protect (``handle.parent_fd``
    is ``None``, for example the root is ``/``, ``.``, or ``..``), there is nothing this function
    can re-verify; it is a no-op, mirroring the documented limitation of
    ``_open_repository_root_fd`` for that case.

    Otherwise the root's own leaf name is reopened fresh -- with the identical
    ``O_DIRECTORY | O_NOFOLLOW``, descriptor-relative discipline used to obtain ``handle.root_fd``
    in the first place, relative to the retained trusted parent descriptor (``handle.parent_fd``)
    -- purely to compare identity by ``fstat`` against ``handle.identity``, the ``(st_dev,
    st_ino)`` pair captured when ``handle.root_fd`` was first opened. The freshly opened
    descriptor is discarded immediately afterward and is never substituted for ``handle.root_fd``,
    so every actual bound-input and output operation always goes through the original retained
    root descriptor alone. Calling this both immediately before and immediately after publication
    turns a root-level name swap -- whether it happens while the root descriptor is idle or during
    the publish itself -- into a stable, nonzero, governed ``REPOSITORY_ROOT_REPLACED`` error
    rather than a successful return value, even when complete, correctly hashed bytes happen to
    exist under the retained root descriptor: a name swap observed after publication has already
    made the document durable is reported as a governed failure, not as license to roll back an
    already-published file.
    """

    if handle.parent_fd is None or handle.leaf_name is None:
        return

    try:
        fresh_fd = os.open(
            handle.leaf_name,
            os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW,
            dir_fd=handle.parent_fd,
        )
    except OSError as exc:
        raise GovernanceHashBoundDocumentError(
            "REPOSITORY_ROOT_REPLACED",
            f"repository root name binding could not be re-verified {stage} publication "
            f"(errno={exc.errno})",
        ) from exc

    try:
        fresh_identity = _fd_identity(
            fresh_fd, stage=stage, code="REPOSITORY_ROOT_REPLACED", subject="repository root"
        )
    except BaseException:
        _close_best_effort(fresh_fd)
        raise
    _close_or_raise(
        fresh_fd,
        code="REPOSITORY_ROOT_VERIFICATION_CLOSE_FAILED",
        detail=(
            "the freshly-resolved repository root verification descriptor could not be closed "
            f"{stage} publication"
        ),
    )

    if fresh_identity != handle.identity:
        if stage == "before":
            detail = (
                "repository root directory was replaced before publication; the governed "
                "document was not written"
            )
        else:
            detail = (
                "repository root directory was replaced during publication; complete, "
                "correctly hashed bytes may exist under the retained root descriptor, but this "
                "call will not report success for a pathname whose root no longer matches the "
                "retained descriptor, and no rollback was attempted"
            )
        raise GovernanceHashBoundDocumentError("REPOSITORY_ROOT_REPLACED", detail)


# ---------------------------------------------------------------------------
# Orchestration
# ---------------------------------------------------------------------------


def _write_governed_document_under_root(
    *,
    root_handle: _RepositoryRootHandle,
    root_display: Path,
    template_text: str,
    bindings: Sequence[Binding],
    output_relative_path: str,
) -> Path:
    """The body of ``write_governed_document`` that runs with ``root_handle`` already open.

    Closing ``root_handle.root_fd`` and ``root_handle.parent_fd`` is the caller's responsibility,
    so that the caller can apply the same otherwise-successful-vs-already-failing close
    precedence uniformly at the one place that owns those descriptors' lifetimes.
    """

    root_fd = root_handle.root_fd
    _validate_template(template_text)
    normalized_bindings = _validate_binding_labels_and_paths(bindings)

    output_normalized = _validate_relative_posix_path(
        output_relative_path,
        malformed_code="OUTPUT_PATH_MALFORMED",
        outside_root_code="OUTPUT_PATH_OUTSIDE_ROOT",
    )
    output_text = output_normalized.as_posix()
    for binding in normalized_bindings:
        if binding.relative_path == output_text:
            raise GovernanceHashBoundDocumentError(
                "OUTPUT_ALIASES_INPUT",
                f"output path aliases a bound input path: {output_text!r}",
            )

    resolved_rows: list[tuple[Binding, int, str]] = []
    for binding in normalized_bindings:
        relative = PurePosixPath(binding.relative_path)
        file_fd = _descend_to_file(root_fd, relative)
        try:
            size, digest = _hash_fd_and_detect_mutation(file_fd, binding.relative_path)
        except BaseException:
            _close_best_effort(file_fd)
            raise
        _close_or_raise(
            file_fd,
            code="BINDING_PATH_CLOSE_FAILED",
            detail=f"bound input descriptor could not be closed: {binding.relative_path!r}",
        )
        resolved_rows.append((binding, size, digest))

    block_text = _build_hash_block(resolved_rows)
    rendered_text = template_text.replace(PLACEHOLDER, block_text, 1)
    final_bytes = rendered_text.encode("utf-8")

    parent_fd, final_name, owns_parent_fd = _descend_to_output_parent(
        root_fd, output_normalized
    )
    try:
        _verify_root_binding_unchanged(root_handle, stage="before")
        _verify_output_parent_binding_unchanged(
            root_fd, output_normalized, parent_fd, stage="before"
        )
        _atomic_publish(parent_fd, final_name, final_bytes)
        _verify_output_parent_binding_unchanged(
            root_fd, output_normalized, parent_fd, stage="after"
        )
        _verify_root_binding_unchanged(root_handle, stage="after")
    except BaseException:
        if owns_parent_fd:
            _close_best_effort(parent_fd)
        raise
    if owns_parent_fd:
        _close_or_raise(
            parent_fd,
            code="OUTPUT_PARENT_CLOSE_FAILED",
            detail="output parent directory descriptor could not be closed",
        )

    return root_display / output_normalized


def write_governed_document(
    *,
    repository_root: Path,
    template_text: str,
    bindings: Sequence[Binding],
    output_relative_path: str,
) -> Path:
    """Validate every input, render the hash-bound document, and publish it atomically.

    A success return value is the requested absolute path of the newly created document, and
    means that path's repository-root and output-parent name bindings each matched their retained
    descriptors at the final observation taken immediately after publication. It is not a claim
    that the returned pathname remains bound to that same directory forever: POSIX offers no way
    to guarantee that a pathname keeps naming the same directory beyond the moment it was last
    observed, and this function performs no check after that final observation. Raises
    ``GovernanceHashBoundDocumentError`` for every governed rejection class -- including a
    repository-root or output-parent name swap detected before or during publication -- and never
    leaves a partially written or overwritten file behind.
    """

    _require_descriptor_relative_capability()
    _require_fclonefileat_capability()
    root_display = _repository_root_display_path(repository_root)
    root_handle = _open_repository_root_fd(repository_root)
    try:
        result = _write_governed_document_under_root(
            root_handle=root_handle,
            root_display=root_display,
            template_text=template_text,
            bindings=bindings,
            output_relative_path=output_relative_path,
        )
    except BaseException:
        _close_best_effort(root_handle.root_fd)
        if root_handle.parent_fd is not None:
            _close_best_effort(root_handle.parent_fd)
        raise
    if root_handle.parent_fd is not None:
        _close_or_raise(
            root_handle.parent_fd,
            code="REPOSITORY_ROOT_PARENT_CLOSE_FAILED",
            detail="repository root parent directory descriptor could not be closed",
        )
    _close_or_raise(
        root_handle.root_fd,
        code="REPOSITORY_ROOT_CLOSE_FAILED",
        detail="repository root descriptor could not be closed",
    )
    return result


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------


def _parse_bindings(raw_values: Sequence[str]) -> list[Binding]:
    bindings: list[Binding] = []
    for raw in raw_values:
        if "=" not in raw:
            raise GovernanceHashBoundDocumentError(
                "BINDING_ARGUMENT_MALFORMED", f"binding is not LABEL=RELATIVE_PATH: {raw!r}"
            )
        label, _, relative_path = raw.partition("=")
        bindings.append(Binding(label=label, relative_path=relative_path))
    return bindings


class _GovernedArgumentParser(argparse.ArgumentParser):
    """An argument parser that raises a governed error instead of printing and exiting."""

    def error(self, message: str) -> None:
        raise GovernanceHashBoundDocumentError("CLI_ARGUMENTS_INVALID", message)


def _parser() -> _GovernedArgumentParser:
    parser = _GovernedArgumentParser(
        description=(
            "Render a governed Markdown document by substituting a single complete-block "
            "placeholder with a machine-computed SHA-256 hash-bound block, then publish the "
            "result once with atomic, never-overwriting semantics. The template is read from "
            "stdin as UTF-8."
        )
    )
    parser.add_argument(
        "--repository-root",
        type=Path,
        required=True,
        help="explicit repository root that bounds every input and output path",
    )
    parser.add_argument(
        "--output",
        required=True,
        metavar="RELATIVE_PATH",
        help="repository-relative destination path for the rendered document",
    )
    parser.add_argument(
        "--binding",
        action="append",
        required=True,
        metavar="LABEL=RELATIVE_PATH",
        help="ordered LABEL=RELATIVE_PATH binding; repeat to bind more than one input file",
    )
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    try:
        args = _parser().parse_args(argv)
        bindings = _parse_bindings(args.binding)
        try:
            raw_stdin = sys.stdin.buffer.read()
        except OSError as exc:
            raise GovernanceHashBoundDocumentError(
                "STDIN_READ_FAILED",
                f"could not read the template from stdin (errno={getattr(exc, 'errno', None)})",
            ) from exc
        template_text = _decode_utf8_template(raw_stdin)
        output_path = write_governed_document(
            repository_root=args.repository_root,
            template_text=template_text,
            bindings=bindings,
            output_relative_path=args.output,
        )
    except GovernanceHashBoundDocumentError as exc:
        print(f"ERROR {exc.code}: {exc.detail}", file=sys.stderr)
        return 1
    print(str(output_path))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
