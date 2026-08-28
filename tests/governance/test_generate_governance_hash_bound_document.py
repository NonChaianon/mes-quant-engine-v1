from __future__ import annotations

import errno
import hashlib
import io
import os
import sys
from pathlib import Path

import pytest

PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from tools import generate_governance_hash_bound_document as module

Binding = module.Binding
GovernanceHashBoundDocumentError = module.GovernanceHashBoundDocumentError
PLACEHOLDER = module.PLACEHOLDER


def _write(root: Path, relative: str, data: bytes) -> Path:
    path = root / relative
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(data)
    return path


def _expected_block(rows: list[tuple[str, str, bytes]]) -> str:
    lines = [
        module.HASH_BLOCK_BEGIN,
        "| Label | Path | Bytes | SHA-256 |",
        "| --- | --- | --- | --- |",
    ]
    for label, relative_path, data in rows:
        digest = hashlib.sha256(data).hexdigest()
        lines.append(f"| {label} | `{relative_path}` | {len(data)} | `{digest}` |")
    lines.append(module.HASH_BLOCK_END)
    return "\n".join(lines)


def _split_hex_digest(separator: str) -> str:
    return separator.join(f"{i % 16:x}" for i in range(64))


def _stray_temp_files(root: Path, final_name: str) -> list[Path]:
    """Return any leftover private temporary-publication files directly under ``root``.

    The rendered document's not-yet-published bytes are written to a randomly named, mode-0600
    regular file directly under the output's parent directory (see the ``.mestmp``-suffixed
    names produced by
    ``generate_governance_hash_bound_document._random_temp_name``), and that name is unlinked
    from the directory's own listing *before* a single byte is written to it -- so under correct
    operation this glob is always empty, even mid-publish. ``final_name`` is accepted for
    call-site symmetry with earlier assertions but does not narrow the glob, since the temporary
    file's random name carries no relationship to the final published name.
    """

    del final_name
    return list(root.glob(f".*{module._TEMP_FILE_SUFFIX}"))


# ---------------------------------------------------------------------------
# Deterministic exact output
# ---------------------------------------------------------------------------


def test_exact_deterministic_output_matches_hand_computed_block(tmp_path: Path) -> None:
    payload = b"alpha input bytes\nsecond line\n"
    _write(tmp_path, "inputs/alpha.txt", payload)
    template = f"# Title\n\nIntro text.\n\n{PLACEHOLDER}\n\nEnd of document.\n"

    output_path = module.write_governed_document(
        repository_root=tmp_path,
        template_text=template,
        bindings=[Binding("ALPHA_FILE", "inputs/alpha.txt")],
        output_relative_path="OUTPUT.md",
    )

    expected_block = _expected_block([("ALPHA_FILE", "inputs/alpha.txt", payload)])
    expected_text = template.replace(PLACEHOLDER, expected_block, 1)

    assert output_path == (tmp_path / "OUTPUT.md")
    assert output_path.read_bytes() == expected_text.encode("utf-8")


def test_repeated_runs_with_identical_inputs_are_byte_identical(tmp_path: Path) -> None:
    payload = b"deterministic bytes"
    _write(tmp_path, "input.txt", payload)
    template = f"Header\n{PLACEHOLDER}\nFooter\n"
    bindings = [Binding("THE_INPUT", "input.txt")]

    first = module.write_governed_document(
        repository_root=tmp_path,
        template_text=template,
        bindings=bindings,
        output_relative_path="one.md",
    )
    second = module.write_governed_document(
        repository_root=tmp_path,
        template_text=template,
        bindings=bindings,
        output_relative_path="two.md",
    )

    assert first.read_bytes() == second.read_bytes()


def test_binding_order_is_preserved_in_the_rendered_block(tmp_path: Path) -> None:
    _write(tmp_path, "a.txt", b"aaa")
    _write(tmp_path, "b.txt", b"bbb")
    template = f"{PLACEHOLDER}\n"

    output_path = module.write_governed_document(
        repository_root=tmp_path,
        template_text=template,
        bindings=[Binding("FIRST", "a.txt"), Binding("SECOND", "b.txt")],
        output_relative_path="ordered.md",
    )

    text = output_path.read_text(encoding="utf-8")
    assert text.index("FIRST") < text.index("SECOND")


def test_cli_main_produces_the_same_bytes_as_the_direct_call(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    payload = b"cli payload bytes"
    _write(tmp_path, "cli_input.txt", payload)
    template = f"CLI\n{PLACEHOLDER}\n"

    direct_output = module.write_governed_document(
        repository_root=tmp_path,
        template_text=template,
        bindings=[Binding("CLI_INPUT", "cli_input.txt")],
        output_relative_path="direct.md",
    )

    fake_stdin = type("FakeStdin", (), {"buffer": io.BytesIO(template.encode("utf-8"))})()
    monkeypatch.setattr(module.sys, "stdin", fake_stdin)

    exit_code = module.main(
        [
            "--repository-root",
            str(tmp_path),
            "--output",
            "cli.md",
            "--binding",
            "CLI_INPUT=cli_input.txt",
        ]
    )

    captured = capsys.readouterr()
    assert exit_code == 0
    assert (tmp_path / "cli.md").read_bytes() == direct_output.read_bytes()
    assert captured.out.strip() == str(tmp_path / "cli.md")


def test_same_output_path_is_rejected_on_a_second_call(tmp_path: Path) -> None:
    _write(tmp_path, "input.txt", b"payload")
    template = f"{PLACEHOLDER}\n"
    bindings = [Binding("INPUT", "input.txt")]

    first = module.write_governed_document(
        repository_root=tmp_path,
        template_text=template,
        bindings=bindings,
        output_relative_path="out.md",
    )
    first_bytes = first.read_bytes()

    with pytest.raises(GovernanceHashBoundDocumentError) as excinfo:
        module.write_governed_document(
            repository_root=tmp_path,
            template_text=template,
            bindings=bindings,
            output_relative_path="out.md",
        )

    assert excinfo.value.code == "OUTPUT_PATH_EXISTS"
    assert first.read_bytes() == first_bytes
    assert _stray_temp_files(tmp_path, "out.md") == []


# ---------------------------------------------------------------------------
# Template rejection classes
# ---------------------------------------------------------------------------


def test_rejects_raw_sha256_text_in_template(tmp_path: Path) -> None:
    _write(tmp_path, "input.txt", b"payload")
    template = f"{PLACEHOLDER}\n\nHand-typed hash: {'a' * 64}\n"

    with pytest.raises(GovernanceHashBoundDocumentError) as excinfo:
        module.write_governed_document(
            repository_root=tmp_path,
            template_text=template,
            bindings=[Binding("INPUT", "input.txt")],
            output_relative_path="out.md",
        )

    assert excinfo.value.code == "TEMPLATE_CONTAINS_RAW_SHA256"
    assert not (tmp_path / "out.md").exists()


def test_rejects_whitespace_split_digest_in_template(tmp_path: Path) -> None:
    _write(tmp_path, "input.txt", b"payload")
    obfuscated = _split_hex_digest(" ")
    template = f"{PLACEHOLDER}\n\nHand-typed hash pieces: {obfuscated}\n"

    with pytest.raises(GovernanceHashBoundDocumentError) as excinfo:
        module.write_governed_document(
            repository_root=tmp_path,
            template_text=template,
            bindings=[Binding("INPUT", "input.txt")],
            output_relative_path="out.md",
        )

    assert excinfo.value.code == "TEMPLATE_CONTAINS_WHITESPACE_SPLIT_DIGEST"
    assert not (tmp_path / "out.md").exists()


def test_rejects_unicode_format_character_split_digest_in_template(tmp_path: Path) -> None:
    _write(tmp_path, "input.txt", b"payload")
    zero_width_space = "\u200b"
    obfuscated = _split_hex_digest(zero_width_space)
    template = f"{PLACEHOLDER}\n\nHand-typed hash pieces: {obfuscated}\n"

    with pytest.raises(GovernanceHashBoundDocumentError) as excinfo:
        module.write_governed_document(
            repository_root=tmp_path,
            template_text=template,
            bindings=[Binding("INPUT", "input.txt")],
            output_relative_path="out.md",
        )

    assert excinfo.value.code == "TEMPLATE_CONTAINS_FORMAT_CHARACTER_SPLIT_DIGEST"
    assert not (tmp_path / "out.md").exists()


def test_rejects_markdown_html_separator_split_digest_in_template(tmp_path: Path) -> None:
    _write(tmp_path, "input.txt", b"payload")
    obfuscated = _split_hex_digest("`")
    template = f"{PLACEHOLDER}\n\nHand-typed hash pieces: {obfuscated}\n"

    with pytest.raises(GovernanceHashBoundDocumentError) as excinfo:
        module.write_governed_document(
            repository_root=tmp_path,
            template_text=template,
            bindings=[Binding("INPUT", "input.txt")],
            output_relative_path="out.md",
        )

    assert excinfo.value.code == "TEMPLATE_CONTAINS_MARKUP_SPLIT_DIGEST"
    assert not (tmp_path / "out.md").exists()


@pytest.mark.parametrize(
    "template",
    [
        "no placeholder here\n",
        f"{PLACEHOLDER}\nduplicate below\n{PLACEHOLDER}\n",
    ],
)
def test_rejects_wrong_placeholder_count(tmp_path: Path, template: str) -> None:
    _write(tmp_path, "input.txt", b"payload")

    with pytest.raises(GovernanceHashBoundDocumentError) as excinfo:
        module.write_governed_document(
            repository_root=tmp_path,
            template_text=template,
            bindings=[Binding("INPUT", "input.txt")],
            output_relative_path="out.md",
        )

    assert excinfo.value.code == "TEMPLATE_PLACEHOLDER_COUNT_INVALID"
    assert not (tmp_path / "out.md").exists()


def test_rejects_placeholder_that_is_not_its_own_complete_line(tmp_path: Path) -> None:
    _write(tmp_path, "input.txt", b"payload")
    template = f"prefix text {PLACEHOLDER} suffix text\n"

    with pytest.raises(GovernanceHashBoundDocumentError) as excinfo:
        module.write_governed_document(
            repository_root=tmp_path,
            template_text=template,
            bindings=[Binding("INPUT", "input.txt")],
            output_relative_path="out.md",
        )

    assert excinfo.value.code == "TEMPLATE_PLACEHOLDER_NOT_OWN_LINE"
    assert not (tmp_path / "out.md").exists()


@pytest.mark.parametrize("marker", [module.HASH_BLOCK_BEGIN, module.HASH_BLOCK_END])
def test_rejects_template_containing_generated_control_markers(tmp_path: Path, marker: str) -> None:
    _write(tmp_path, "input.txt", b"payload")
    template = f"{marker}\n{PLACEHOLDER}\n"

    with pytest.raises(GovernanceHashBoundDocumentError) as excinfo:
        module.write_governed_document(
            repository_root=tmp_path,
            template_text=template,
            bindings=[Binding("INPUT", "input.txt")],
            output_relative_path="out.md",
        )

    assert excinfo.value.code == "TEMPLATE_CONTAINS_CONTROL_MARKER"
    assert not (tmp_path / "out.md").exists()


# ---------------------------------------------------------------------------
# Input rejection classes
# ---------------------------------------------------------------------------


def test_rejects_missing_input(tmp_path: Path) -> None:
    template = f"{PLACEHOLDER}\n"

    with pytest.raises(GovernanceHashBoundDocumentError) as excinfo:
        module.write_governed_document(
            repository_root=tmp_path,
            template_text=template,
            bindings=[Binding("MISSING", "does_not_exist.txt")],
            output_relative_path="out.md",
        )

    assert excinfo.value.code == "BINDING_PATH_MISSING"
    assert not (tmp_path / "out.md").exists()


def test_rejects_directory_as_input(tmp_path: Path) -> None:
    (tmp_path / "a_directory").mkdir()
    template = f"{PLACEHOLDER}\n"

    with pytest.raises(GovernanceHashBoundDocumentError) as excinfo:
        module.write_governed_document(
            repository_root=tmp_path,
            template_text=template,
            bindings=[Binding("DIR", "a_directory")],
            output_relative_path="out.md",
        )

    assert excinfo.value.code == "BINDING_PATH_IS_DIRECTORY"
    assert not (tmp_path / "out.md").exists()


def test_rejects_symlink_as_input(tmp_path: Path) -> None:
    target = _write(tmp_path, "real.txt", b"real bytes")
    link = tmp_path / "link.txt"
    os.symlink(target, link)
    template = f"{PLACEHOLDER}\n"

    with pytest.raises(GovernanceHashBoundDocumentError) as excinfo:
        module.write_governed_document(
            repository_root=tmp_path,
            template_text=template,
            bindings=[Binding("LINK", "link.txt")],
            output_relative_path="out.md",
        )

    assert excinfo.value.code == "BINDING_PATH_IS_SYMLINK"
    assert not (tmp_path / "out.md").exists()
    assert target.read_bytes() == b"real bytes"


def test_rejects_binding_path_outside_root(tmp_path: Path) -> None:
    template = f"{PLACEHOLDER}\n"

    with pytest.raises(GovernanceHashBoundDocumentError) as excinfo:
        module.write_governed_document(
            repository_root=tmp_path,
            template_text=template,
            bindings=[Binding("ESCAPE", "../escape.txt")],
            output_relative_path="out.md",
        )

    assert excinfo.value.code == "BINDING_PATH_OUTSIDE_ROOT"
    assert not (tmp_path / "out.md").exists()


@pytest.mark.parametrize(
    "bad_path",
    ["/absolute/path.txt", "a\\b.txt", "a//b.txt", "a/./b.txt", "trailing/slash/"],
)
def test_rejects_malformed_non_posix_binding_paths(tmp_path: Path, bad_path: str) -> None:
    template = f"{PLACEHOLDER}\n"

    with pytest.raises(GovernanceHashBoundDocumentError) as excinfo:
        module.write_governed_document(
            repository_root=tmp_path,
            template_text=template,
            bindings=[Binding("BAD", bad_path)],
            output_relative_path="out.md",
        )

    assert excinfo.value.code == "BINDING_PATH_MALFORMED"
    assert not (tmp_path / "out.md").exists()


def test_rejects_duplicate_labels(tmp_path: Path) -> None:
    _write(tmp_path, "a.txt", b"a")
    _write(tmp_path, "b.txt", b"b")
    template = f"{PLACEHOLDER}\n"

    with pytest.raises(GovernanceHashBoundDocumentError) as excinfo:
        module.write_governed_document(
            repository_root=tmp_path,
            template_text=template,
            bindings=[Binding("SAME", "a.txt"), Binding("SAME", "b.txt")],
            output_relative_path="out.md",
        )

    assert excinfo.value.code == "BINDING_LABEL_DUPLICATE"
    assert not (tmp_path / "out.md").exists()


def test_rejects_duplicate_paths(tmp_path: Path) -> None:
    _write(tmp_path, "a.txt", b"a")
    template = f"{PLACEHOLDER}\n"

    with pytest.raises(GovernanceHashBoundDocumentError) as excinfo:
        module.write_governed_document(
            repository_root=tmp_path,
            template_text=template,
            bindings=[Binding("FIRST", "a.txt"), Binding("SECOND", "a.txt")],
            output_relative_path="out.md",
        )

    assert excinfo.value.code == "BINDING_PATH_DUPLICATE"
    assert not (tmp_path / "out.md").exists()


def test_rejects_invalid_label(tmp_path: Path) -> None:
    _write(tmp_path, "a.txt", b"a")
    template = f"{PLACEHOLDER}\n"

    with pytest.raises(GovernanceHashBoundDocumentError) as excinfo:
        module.write_governed_document(
            repository_root=tmp_path,
            template_text=template,
            bindings=[Binding("not-upper-case", "a.txt")],
            output_relative_path="out.md",
        )

    assert excinfo.value.code == "BINDING_LABEL_INVALID"
    assert not (tmp_path / "out.md").exists()


# ---------------------------------------------------------------------------
# Output rejection classes
# ---------------------------------------------------------------------------


def test_rejects_unsafe_output_path_absolute(tmp_path: Path) -> None:
    _write(tmp_path, "a.txt", b"a")
    template = f"{PLACEHOLDER}\n"

    with pytest.raises(GovernanceHashBoundDocumentError) as excinfo:
        module.write_governed_document(
            repository_root=tmp_path,
            template_text=template,
            bindings=[Binding("INPUT", "a.txt")],
            output_relative_path="/tmp/escape.md",
        )

    assert excinfo.value.code == "OUTPUT_PATH_MALFORMED"


def test_rejects_unsafe_output_path_missing_parent(tmp_path: Path) -> None:
    _write(tmp_path, "a.txt", b"a")
    template = f"{PLACEHOLDER}\n"

    with pytest.raises(GovernanceHashBoundDocumentError) as excinfo:
        module.write_governed_document(
            repository_root=tmp_path,
            template_text=template,
            bindings=[Binding("INPUT", "a.txt")],
            output_relative_path="no_such_dir/out.md",
        )

    assert excinfo.value.code == "OUTPUT_PARENT_MISSING"


def test_rejects_existing_output_and_never_overwrites_it(tmp_path: Path) -> None:
    _write(tmp_path, "a.txt", b"a")
    sentinel = b"SENTINEL BYTES DO NOT TOUCH"
    _write(tmp_path, "out.md", sentinel)
    template = f"{PLACEHOLDER}\n"

    with pytest.raises(GovernanceHashBoundDocumentError) as excinfo:
        module.write_governed_document(
            repository_root=tmp_path,
            template_text=template,
            bindings=[Binding("INPUT", "a.txt")],
            output_relative_path="out.md",
        )

    assert excinfo.value.code == "OUTPUT_PATH_EXISTS"
    assert (tmp_path / "out.md").read_bytes() == sentinel
    assert _stray_temp_files(tmp_path, "out.md") == []


def test_rejects_output_symlink_and_never_writes_through_it(tmp_path: Path) -> None:
    _write(tmp_path, "a.txt", b"a")
    target = _write(tmp_path, "real_target.txt", b"TARGET SENTINEL")
    link = tmp_path / "out.md"
    os.symlink(target, link)
    template = f"{PLACEHOLDER}\n"

    with pytest.raises(GovernanceHashBoundDocumentError) as excinfo:
        module.write_governed_document(
            repository_root=tmp_path,
            template_text=template,
            bindings=[Binding("INPUT", "a.txt")],
            output_relative_path="out.md",
        )

    assert excinfo.value.code == "OUTPUT_PATH_IS_SYMLINK"
    assert link.is_symlink()
    assert target.read_bytes() == b"TARGET SENTINEL"
    assert _stray_temp_files(tmp_path, "out.md") == []


def test_rejects_output_input_aliasing_and_leaves_input_untouched(tmp_path: Path) -> None:
    payload = b"aliasing target bytes"
    input_path = _write(tmp_path, "shared.txt", payload)
    template = f"{PLACEHOLDER}\n"

    with pytest.raises(GovernanceHashBoundDocumentError) as excinfo:
        module.write_governed_document(
            repository_root=tmp_path,
            template_text=template,
            bindings=[Binding("SHARED", "shared.txt")],
            output_relative_path="shared.txt",
        )

    assert excinfo.value.code == "OUTPUT_ALIASES_INPUT"
    assert input_path.read_bytes() == payload


def test_cli_rejects_non_utf8_stdin(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    _write(tmp_path, "input.txt", b"payload")
    fake_stdin = type("FakeStdin", (), {"buffer": io.BytesIO(b"\xff\xfe not utf-8")})()
    monkeypatch.setattr(module.sys, "stdin", fake_stdin)

    exit_code = module.main(
        [
            "--repository-root",
            str(tmp_path),
            "--output",
            "out.md",
            "--binding",
            "INPUT=input.txt",
        ]
    )

    captured = capsys.readouterr()
    assert exit_code == 1
    assert not (tmp_path / "out.md").exists()
    # The detail is an exact, fixed, host-independent literal: never
    # ``UnicodeDecodeError.__str__`` (whose codec-name/byte-offset/reason wording is not a value
    # this module treats as stable across platforms or Python versions), and never a traceback.
    assert captured.err == "ERROR TEMPLATE_NOT_UTF8: template stdin is not valid UTF-8\n"
    assert captured.out == ""
    assert "Traceback" not in captured.err
    assert "codec" not in captured.err
    assert "byte" not in captured.err


def test_cli_reports_a_governed_code_for_argument_errors(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    exit_code = module.main(
        [
            "--repository-root",
            str(tmp_path),
            "--binding",
            "INPUT=input.txt",
        ]
    )

    captured = capsys.readouterr()
    assert exit_code == 1
    assert "ERROR CLI_ARGUMENTS_INVALID:" in captured.err


def test_cli_reports_a_governed_code_for_stdin_read_failure(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    _write(tmp_path, "input.txt", b"payload")

    class _FailingBuffer:
        def read(self) -> bytes:
            raise OSError(5, "simulated I/O failure")

    fake_stdin = type("FakeStdin", (), {"buffer": _FailingBuffer()})()
    monkeypatch.setattr(module.sys, "stdin", fake_stdin)

    exit_code = module.main(
        [
            "--repository-root",
            str(tmp_path),
            "--output",
            "out.md",
            "--binding",
            "INPUT=input.txt",
        ]
    )

    assert exit_code == 1
    assert not (tmp_path / "out.md").exists()


def test_capability_gate_fails_closed_when_dir_fd_support_is_absent(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    _write(tmp_path, "input.txt", b"payload")
    template = f"{PLACEHOLDER}\n"

    monkeypatch.setattr(module.os, "supports_dir_fd", frozenset())

    with pytest.raises(GovernanceHashBoundDocumentError) as excinfo:
        module.write_governed_document(
            repository_root=tmp_path,
            template_text=template,
            bindings=[Binding("INPUT", "input.txt")],
            output_relative_path="out.md",
        )

    assert excinfo.value.code == "CAPABILITY_DIR_FD_UNSUPPORTED"


# ---------------------------------------------------------------------------
# TOCTOU adversarial tests: repository root
# ---------------------------------------------------------------------------


def test_repository_root_replacement_after_open_fails_closed_before_publication(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Swapping the repository-root directory for a fresh, empty directory of the same name,
    immediately after the root has been opened as a descriptor, must never let the call return a
    stale pathname as though it had succeeded.

    The previous implementation validated the repository root with a pathname-based check
    (``Path.resolve(strict=True)`` plus ``is_dir()``) and then reopened that same pathname string
    in a second, independent ``os.open`` call. Between those two steps, an attacker able to
    replace the directory named by that pathname could redirect every subsequent bound-input and
    output operation into the replacement -- a classic checked-then-reopen TOCTOU. The current
    implementation opens the root's final path component exactly once, relative to its
    already-open parent, with ``O_DIRECTORY | O_NOFOLLOW``, and binds its identity with ``fstat``
    at that same moment; the returned descriptor -- never a re-resolved pathname -- is used for
    every real read or write operation, so a swap performed immediately after that open cannot
    redirect any bound-input or output access. But the retained root descriptor alone cannot make
    a *returned pathname* trustworthy once the name it names has drifted: the trusted parent
    descriptor and root leaf name are retained precisely so the root's name binding can be
    re-verified, by fresh ``fstat``-identity comparison, immediately before publication. Complete,
    correctly hashed bytes could in principle still be produced under the retained descriptor, but
    this module must not report success for a repository-root pathname that no longer identifies
    the directory that was actually opened, so it fails closed with a stable, nonzero
    ``REPOSITORY_ROOT_REPLACED`` error and writes nothing at all.
    """

    root_dir = tmp_path / "governed_root"
    root_dir.mkdir()
    _write(root_dir, "input.txt", b"ORIGINAL ROOT BYTES")
    template = f"{PLACEHOLDER}\n"

    real_open = module.os.open
    state = {"swapped": False}

    def fake_open(path, flags, mode=0o777, *, dir_fd=None):  # type: ignore[no-untyped-def]
        if dir_fd is None:
            fd = real_open(path, flags, mode)
        else:
            fd = real_open(path, flags, mode, dir_fd=dir_fd)
        if (
            not state["swapped"]
            and dir_fd is not None
            and path == root_dir.name
            and flags & os.O_NOFOLLOW
            and flags & os.O_DIRECTORY
        ):
            state["swapped"] = True
            os.rename(str(root_dir), str(tmp_path / "governed_root_original"))
            os.mkdir(str(root_dir))
        return fd

    monkeypatch.setattr(module.os, "open", fake_open)

    with pytest.raises(GovernanceHashBoundDocumentError) as excinfo:
        module.write_governed_document(
            repository_root=root_dir,
            template_text=template,
            bindings=[Binding("INPUT", "input.txt")],
            output_relative_path="out.md",
        )

    assert state["swapped"] is True
    assert excinfo.value.code == "REPOSITORY_ROOT_REPLACED"
    assert not (root_dir / "out.md").exists()
    assert not (tmp_path / "governed_root_original" / "out.md").exists()


def test_repository_root_replacement_during_publication_fails_closed_after_publish(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """A repository-root name swap performed during publication -- after the atomic
    ``fclonefileat`` clone has already made the document durably visible under the original root
    directory's identity, but before ``write_governed_document`` returns -- must never let the
    caller receive a return value or CLI stdout line naming a pathname that no longer identifies
    the directory the document actually lives in.

    For an output path with no subdirectory the output "parent" directory is the repository root
    itself, and ``_descend_to_output_parent`` reuses the already-open root descriptor rather than
    performing an independent pathname reopen -- so the output-parent re-verification alone is a
    no-op for this case (it compares the retained root descriptor's identity against itself). The
    dedicated root-binding re-verification is what detects a swap here: the already-published
    bytes are never rolled back (this module never attempts to undo an already-durable publish),
    but the post-publish root-identity re-verification still turns the call into a stable,
    nonzero, governed ``REPOSITORY_ROOT_REPLACED`` failure instead of silently reporting the stale
    pathname, even though complete, correctly hashed bytes exist under the retained descriptor.
    """

    root_dir = tmp_path / "governed_root"
    root_dir.mkdir()
    _write(root_dir, "input.txt", b"ORIGINAL ROOT BYTES")
    template = f"{PLACEHOLDER}\n"

    real_invoke = module._invoke_fclonefileat
    state = {"swapped": False}

    def fake_invoke(src_fd, dst_dir_fd, dst_name):  # type: ignore[no-untyped-def]
        result = real_invoke(src_fd, dst_dir_fd, dst_name)
        if not state["swapped"]:
            state["swapped"] = True
            os.rename(str(root_dir), str(tmp_path / "governed_root_original"))
            os.mkdir(str(root_dir))
        return result

    monkeypatch.setattr(module, "_invoke_fclonefileat", fake_invoke)

    with pytest.raises(GovernanceHashBoundDocumentError) as excinfo:
        module.write_governed_document(
            repository_root=root_dir,
            template_text=template,
            bindings=[Binding("INPUT", "input.txt")],
            output_relative_path="out.md",
        )

    assert state["swapped"] is True
    assert excinfo.value.code == "REPOSITORY_ROOT_REPLACED"
    assert not (root_dir / "out.md").exists()
    published = tmp_path / "governed_root_original" / "out.md"
    assert published.exists()
    assert hashlib.sha256(b"ORIGINAL ROOT BYTES").hexdigest() in published.read_text(
        encoding="utf-8"
    )


# ---------------------------------------------------------------------------
# TOCTOU adversarial tests: input side
# ---------------------------------------------------------------------------


def test_input_leaf_replacement_after_open_is_detected_as_a_stable_mutation_and_produces_no_output(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Unlinking and replacing the bound leaf mid-read never lets the replacement bytes reach a
    published document.

    The retained descriptor keeps referencing the original inode's data (POSIX unlink-while-open
    semantics), so a naive content-only comparison could be tempted to call this "safe" and still
    publish a hash bound to the original bytes. But the unlink itself is an observable metadata
    mutation of the file identity this module is holding open (its link count drops and its
    ctime advances), and the before/after ``fstat`` comparison in
    ``_hash_fd_and_detect_mutation`` correctly treats that as bound-input mutation during read.
    The module fails closed rather than silently deciding, on the caller's behalf, that a
    concurrent unlink was harmless. No output is created, and neither the original nor the
    replacement bytes are ever represented in a published document.
    """

    original = b"ORIGINAL BYTES BOUND TO THE RETAINED DESCRIPTOR"
    replaced = b"REPLACED BYTES MUST NEVER BE HASHED"
    _write(tmp_path, "input.txt", original)
    template = f"{PLACEHOLDER}\n"

    real_read = module.os.read
    state = {"swapped": False}

    def fake_read(fd: int, count: int) -> bytes:
        if not state["swapped"]:
            state["swapped"] = True
            (tmp_path / "input.txt").unlink()
            (tmp_path / "input.txt").write_bytes(replaced)
        return real_read(fd, count)

    monkeypatch.setattr(module.os, "read", fake_read)

    with pytest.raises(GovernanceHashBoundDocumentError) as excinfo:
        module.write_governed_document(
            repository_root=tmp_path,
            template_text=template,
            bindings=[Binding("INPUT", "input.txt")],
            output_relative_path="out.md",
        )

    assert excinfo.value.code == "BINDING_INPUT_MUTATED_DURING_READ"
    assert not (tmp_path / "out.md").exists()
    assert _stray_temp_files(tmp_path, "out.md") == []
    assert hashlib.sha256(original).hexdigest() not in excinfo.value.detail
    assert hashlib.sha256(replaced).hexdigest() not in excinfo.value.detail
    assert (tmp_path / "input.txt").read_bytes() == replaced


def test_input_parent_directory_replacement_after_open_does_not_redirect_traversal(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    (tmp_path / "sub" / "inner").mkdir(parents=True)
    original = b"ORIGINAL NESTED BYTES BEHIND THE RETAINED DIRECTORY DESCRIPTOR"
    _write(tmp_path, "sub/inner/target.txt", original)
    template = f"{PLACEHOLDER}\n"

    real_open = module.os.open
    state = {"swapped": False}

    def fake_open(path, flags, mode=0o777, *, dir_fd=None):  # type: ignore[no-untyped-def]
        if dir_fd is None:
            fd = real_open(path, flags, mode)
        else:
            fd = real_open(path, flags, mode, dir_fd=dir_fd)
        if path == "inner" and dir_fd is not None and not state["swapped"]:
            state["swapped"] = True
            os.rename(str(tmp_path / "sub" / "inner"), str(tmp_path / "sub" / "inner_moved"))
            os.mkdir(str(tmp_path / "sub" / "inner"))
        return fd

    monkeypatch.setattr(module.os, "open", fake_open)

    output_path = module.write_governed_document(
        repository_root=tmp_path,
        template_text=template,
        bindings=[Binding("NESTED", "sub/inner/target.txt")],
        output_relative_path="out.md",
    )

    assert hashlib.sha256(original).hexdigest() in output_path.read_text(encoding="utf-8")
    assert not (tmp_path / "sub" / "inner" / "target.txt").exists()
    assert (tmp_path / "sub" / "inner_moved" / "target.txt").read_bytes() == original


def test_detects_input_mutated_during_read(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    path = _write(tmp_path, "input.txt", b"stable original bytes")
    template = f"{PLACEHOLDER}\n"

    real_read = module.os.read
    state = {"mutated": False}

    def fake_read(fd: int, count: int) -> bytes:
        chunk = real_read(fd, count)
        if not chunk and not state["mutated"]:
            state["mutated"] = True
            with open(path, "ab") as handle:
                handle.write(b"TAIL BYTES APPENDED AFTER THE READ COMPLETED")
        return chunk

    monkeypatch.setattr(module.os, "read", fake_read)

    with pytest.raises(GovernanceHashBoundDocumentError) as excinfo:
        module.write_governed_document(
            repository_root=tmp_path,
            template_text=template,
            bindings=[Binding("INPUT", "input.txt")],
            output_relative_path="out.md",
        )

    assert excinfo.value.code == "BINDING_INPUT_MUTATED_DURING_READ"
    assert not (tmp_path / "out.md").exists()


# ---------------------------------------------------------------------------
# TOCTOU adversarial tests: output side
# ---------------------------------------------------------------------------


def test_output_parent_directory_swap_before_publication_fails_closed_without_writing(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """A parent-directory swap that happens right after the output parent descriptor is opened,
    but before anything is written, must fail closed instead of silently publishing into the
    original (renamed-away) directory under a pathname that would then describe the wrong thing.

    The retained parent descriptor still refers to the original directory (now reachable only as
    ``outdir_original``) by POSIX rename-of-open-directory semantics, so a naive implementation
    could still successfully write there and return/report the now-stale ``outdir/report.md``
    pathname. The pre-publication identity re-verification -- comparing the retained parent
    descriptor against a fresh, independent resolution of the same ``outdir`` pathname -- detects
    that the name no longer identifies the retained directory and fails closed before any bytes
    are written.
    """
    _write(tmp_path, "input.txt", b"payload")
    (tmp_path / "outdir").mkdir()
    template = f"{PLACEHOLDER}\n"

    real_open = module.os.open
    state = {"swapped": False}

    def fake_open(path, flags, mode=0o777, *, dir_fd=None):  # type: ignore[no-untyped-def]
        if dir_fd is None:
            fd = real_open(path, flags, mode)
        else:
            fd = real_open(path, flags, mode, dir_fd=dir_fd)
        if path == "outdir" and dir_fd is not None and not state["swapped"]:
            state["swapped"] = True
            os.rename(str(tmp_path / "outdir"), str(tmp_path / "outdir_original"))
            os.mkdir(str(tmp_path / "outdir"))
        return fd

    monkeypatch.setattr(module.os, "open", fake_open)

    with pytest.raises(GovernanceHashBoundDocumentError) as excinfo:
        module.write_governed_document(
            repository_root=tmp_path,
            template_text=template,
            bindings=[Binding("INPUT", "input.txt")],
            output_relative_path="outdir/report.md",
        )

    assert excinfo.value.code == "OUTPUT_PARENT_REPLACED"
    assert not (tmp_path / "outdir" / "report.md").exists()
    assert not (tmp_path / "outdir_original" / "report.md").exists()
    assert _stray_temp_files(tmp_path / "outdir_original", "report.md") == []


def test_output_parent_directory_swap_during_publication_fails_closed_after_publish(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """A parent-directory swap performed during publication -- after the atomic ``fclonefileat``
    clone has already made the document durably visible under the original directory's identity,
    but before ``write_governed_document`` returns -- must never let the caller receive a return
    value or CLI stdout line naming a pathname (``outdir/report.md``) that no longer identifies
    the directory the document actually lives in.

    The already-published bytes are never rolled back (this module never attempts to undo an
    already-durable publish), but the post-publish parent-identity re-verification still turns
    the call into a stable governed failure instead of silently reporting the stale pathname.
    """
    _write(tmp_path, "input.txt", b"payload")
    (tmp_path / "outdir").mkdir()
    template = f"{PLACEHOLDER}\n"

    real_invoke = module._invoke_fclonefileat
    state = {"swapped": False}

    def fake_invoke(src_fd, dst_dir_fd, dst_name):  # type: ignore[no-untyped-def]
        result = real_invoke(src_fd, dst_dir_fd, dst_name)
        if not state["swapped"]:
            state["swapped"] = True
            os.rename(str(tmp_path / "outdir"), str(tmp_path / "outdir_original"))
            os.mkdir(str(tmp_path / "outdir"))
        return result

    monkeypatch.setattr(module, "_invoke_fclonefileat", fake_invoke)

    with pytest.raises(GovernanceHashBoundDocumentError) as excinfo:
        module.write_governed_document(
            repository_root=tmp_path,
            template_text=template,
            bindings=[Binding("INPUT", "input.txt")],
            output_relative_path="outdir/report.md",
        )

    assert excinfo.value.code == "OUTPUT_PARENT_REPLACED"
    assert not (tmp_path / "outdir" / "report.md").exists()
    published = tmp_path / "outdir_original" / "report.md"
    assert published.exists()
    assert "INPUT" in published.read_text(encoding="utf-8")
    assert _stray_temp_files(tmp_path / "outdir_original", "report.md") == []


def test_temp_pathname_is_unlinked_and_absent_before_any_bytes_are_written(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """The randomly named temporary publication file's own name must already be gone from the
    output-parent directory's listing before this module writes a single content byte to it, and
    it must stay gone through fsync and the publishing clone.

    A same-directory visible temporary name is guessable and, on a shared or group-readable
    parent directory, is observable to anything that can list that directory while bytes are
    still being written. This test captures the temporary file's own randomly generated name at
    the moment it is created, then asserts -- at every later instrumented point, including
    immediately after creation, immediately before the write, and immediately before the
    publishing ``fclonefileat`` call -- that no entry with that name is present in the parent
    directory's listing.
    """

    payload = b"payload bound to a nameless retained descriptor"
    _write(tmp_path, "input.txt", payload)
    template = f"{PLACEHOLDER}\n"

    real_open = module.os.open
    real_unlink = module.os.unlink
    state: dict[str, object] = {"temp_name": None, "unlinked": False}
    observed: dict[str, object] = {}

    def fake_open(path, flags, mode=0o777, *, dir_fd=None):  # type: ignore[no-untyped-def]
        fd = real_open(path, flags, mode, dir_fd=dir_fd)
        if (
            isinstance(path, str)
            and path.endswith(module._TEMP_FILE_SUFFIX)
            and (flags & os.O_CREAT)
            and (flags & os.O_EXCL)
        ):
            state["temp_name"] = path
            # Immediately after creation, the name must still be listed exactly once (the
            # unlink has not happened yet).
            observed["present_immediately_after_create"] = path in os.listdir(tmp_path)
        return fd

    def fake_unlink(path, *, dir_fd=None):  # type: ignore[no-untyped-def]
        result = real_unlink(path, dir_fd=dir_fd)
        if path == state["temp_name"]:
            state["unlinked"] = True
            observed["absent_immediately_after_unlink"] = path not in os.listdir(tmp_path)
        return result

    monkeypatch.setattr(module.os, "open", fake_open)
    monkeypatch.setattr(module.os, "unlink", fake_unlink)

    real_invoke = module._invoke_fclonefileat

    def fake_invoke(src_fd, dst_dir_fd, dst_name):  # type: ignore[no-untyped-def]
        observed["absent_before_clone"] = state["temp_name"] not in os.listdir(tmp_path)
        observed["unlinked_before_clone"] = state["unlinked"] is True
        return real_invoke(src_fd, dst_dir_fd, dst_name)

    monkeypatch.setattr(module, "_invoke_fclonefileat", fake_invoke)

    output_path = module.write_governed_document(
        repository_root=tmp_path,
        template_text=template,
        bindings=[Binding("INPUT", "input.txt")],
        output_relative_path="out.md",
    )

    assert state["temp_name"] is not None
    assert observed["present_immediately_after_create"] is True
    assert observed["absent_immediately_after_unlink"] is True
    assert observed["unlinked_before_clone"] is True
    assert observed["absent_before_clone"] is True
    assert state["temp_name"] not in os.listdir(tmp_path)
    assert hashlib.sha256(payload).hexdigest() in output_path.read_text(encoding="utf-8")
    assert _stray_temp_files(tmp_path, "out.md") == []


def test_fclonefileat_is_invoked_with_the_retained_source_descriptor(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """The publishing clone must be given the exact retained descriptor of the already-written,
    already-unlinked temporary file -- never a freshly (re-)opened descriptor of any name -- as
    its source, so nothing that happens to any pathname after creation can change what gets
    cloned.
    """

    payload = b"bytes that must reach the destination via the retained descriptor"
    _write(tmp_path, "input.txt", payload)
    template = f"{PLACEHOLDER}\n"

    state = _patch_open_to_capture_private_temp_fd(monkeypatch)

    real_invoke = module._invoke_fclonefileat
    observed: dict[str, object] = {}

    def fake_invoke(src_fd, dst_dir_fd, dst_name):  # type: ignore[no-untyped-def]
        observed["src_fd_matches_retained_temp_fd"] = src_fd == state["temp_fd"]
        observed["dst_name"] = dst_name
        return real_invoke(src_fd, dst_dir_fd, dst_name)

    monkeypatch.setattr(module, "_invoke_fclonefileat", fake_invoke)

    output_path = module.write_governed_document(
        repository_root=tmp_path,
        template_text=template,
        bindings=[Binding("INPUT", "input.txt")],
        output_relative_path="out.md",
    )

    assert observed["src_fd_matches_retained_temp_fd"] is True
    assert observed["dst_name"] == "out.md"
    assert hashlib.sha256(payload).hexdigest() in output_path.read_text(encoding="utf-8")


def test_output_is_invisible_under_the_final_name_until_the_atomic_clone(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    _write(tmp_path, "input.txt", b"payload")
    template = f"{PLACEHOLDER}\n"

    real_invoke = module._invoke_fclonefileat
    observed: dict[str, object] = {}

    def fake_invoke(src_fd, dst_dir_fd, dst_name):  # type: ignore[no-untyped-def]
        observed["final_missing_before_clone"] = dst_name not in os.listdir(tmp_path)
        real_invoke(src_fd, dst_dir_fd, dst_name)
        observed["final_present_after_clone"] = dst_name in os.listdir(tmp_path)

    monkeypatch.setattr(module, "_invoke_fclonefileat", fake_invoke)

    output_path = module.write_governed_document(
        repository_root=tmp_path,
        template_text=template,
        bindings=[Binding("INPUT", "input.txt")],
        output_relative_path="out.md",
    )

    assert observed["final_missing_before_clone"] is True
    assert observed["final_present_after_clone"] is True
    assert output_path.exists()


def test_temp_file_fsync_failure_leaves_no_output_and_no_stray_temp(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    _write(tmp_path, "input.txt", b"payload")
    template = f"{PLACEHOLDER}\n"

    def failing_fsync(_fd: int) -> None:
        raise OSError("simulated durability failure")

    monkeypatch.setattr(module.os, "fsync", failing_fsync)

    with pytest.raises(GovernanceHashBoundDocumentError) as excinfo:
        module.write_governed_document(
            repository_root=tmp_path,
            template_text=template,
            bindings=[Binding("INPUT", "input.txt")],
            output_relative_path="out.md",
        )

    assert excinfo.value.code == "OUTPUT_TEMP_FSYNC_FAILED"
    assert not (tmp_path / "out.md").exists()
    assert _stray_temp_files(tmp_path, "out.md") == []


def test_fclonefileat_collision_from_a_concurrent_writer_is_rejected_without_overwrite(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Same-output-never-overwrites, exercised at the ``fclonefileat`` boundary itself: a
    concurrent writer that creates the destination name in the narrow window between this
    module's temporary-file fsync and its publishing clone call must make the clone fail with
    ``EEXIST`` (mapped to the stable ``OUTPUT_PATH_EXISTS`` code), and the racer's bytes -- never
    this module's rendered bytes -- must be exactly what remains under that name.
    """

    _write(tmp_path, "input.txt", b"payload")
    template = f"{PLACEHOLDER}\n"
    racer_bytes = b"RACER WON THE NAME FIRST"

    real_invoke = module._invoke_fclonefileat

    def fake_invoke(src_fd, dst_dir_fd, dst_name):  # type: ignore[no-untyped-def]
        racer_fd = os.open(
            dst_name, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o644, dir_fd=dst_dir_fd
        )
        os.write(racer_fd, racer_bytes)
        os.close(racer_fd)
        return real_invoke(src_fd, dst_dir_fd, dst_name)

    monkeypatch.setattr(module, "_invoke_fclonefileat", fake_invoke)

    with pytest.raises(GovernanceHashBoundDocumentError) as excinfo:
        module.write_governed_document(
            repository_root=tmp_path,
            template_text=template,
            bindings=[Binding("INPUT", "input.txt")],
            output_relative_path="out.md",
        )

    assert excinfo.value.code == "OUTPUT_PATH_EXISTS"
    assert (tmp_path / "out.md").read_bytes() == racer_bytes
    assert _stray_temp_files(tmp_path, "out.md") == []


def test_unsupported_fclonefileat_at_publish_time_fails_closed(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """A volume/filesystem that rejects ``fclonefileat`` with ``ENOTSUP`` at call time (for
    example a non-copy-on-write destination filesystem) must fail closed with a stable governed
    code and must never fall back to any other publication primitive.
    """

    _write(tmp_path, "input.txt", b"payload")
    template = f"{PLACEHOLDER}\n"

    def fake_invoke(src_fd, dst_dir_fd, dst_name):  # type: ignore[no-untyped-def, unused-argument]
        raise OSError(errno.ENOTSUP, "simulated volume without clone support")

    monkeypatch.setattr(module, "_invoke_fclonefileat", fake_invoke)

    with pytest.raises(GovernanceHashBoundDocumentError) as excinfo:
        module.write_governed_document(
            repository_root=tmp_path,
            template_text=template,
            bindings=[Binding("INPUT", "input.txt")],
            output_relative_path="out.md",
        )

    assert excinfo.value.code == "OUTPUT_FCLONEFILEAT_UNSUPPORTED"
    assert not (tmp_path / "out.md").exists()
    assert _stray_temp_files(tmp_path, "out.md") == []


def test_capability_gate_fails_closed_when_fclonefileat_is_unavailable(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """A platform or C-runtime that cannot provide a working ``fclonefileat`` binding at all
    (non-Darwin, missing symbol, or a C-library load failure) must fail closed with the stable
    ``CAPABILITY_FCLONEFILEAT_UNSUPPORTED`` code before any input is read or any output byte is
    written, and must never fall back to a named-link or any other publication primitive.
    """

    _write(tmp_path, "input.txt", b"payload")
    template = f"{PLACEHOLDER}\n"

    def fake_resolve():  # type: ignore[no-untyped-def]
        raise GovernanceHashBoundDocumentError(
            "CAPABILITY_FCLONEFILEAT_UNSUPPORTED",
            "simulated: fclonefileat is not available on this platform",
        )

    monkeypatch.setattr(module, "_resolve_fclonefileat", fake_resolve)

    with pytest.raises(GovernanceHashBoundDocumentError) as excinfo:
        module.write_governed_document(
            repository_root=tmp_path,
            template_text=template,
            bindings=[Binding("INPUT", "input.txt")],
            output_relative_path="out.md",
        )

    assert excinfo.value.code == "CAPABILITY_FCLONEFILEAT_UNSUPPORTED"
    assert not (tmp_path / "out.md").exists()
    assert _stray_temp_files(tmp_path, "out.md") == []


def test_directory_fsync_failure_after_successful_clone_does_not_roll_back(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    _write(tmp_path, "input.txt", b"payload")
    template = f"{PLACEHOLDER}\n"

    real_fsync = module.os.fsync
    calls = {"n": 0}

    def flaky_fsync(fd: int) -> None:
        calls["n"] += 1
        if calls["n"] == 2:
            raise OSError("simulated directory durability failure")
        real_fsync(fd)

    monkeypatch.setattr(module.os, "fsync", flaky_fsync)

    with pytest.raises(GovernanceHashBoundDocumentError) as excinfo:
        module.write_governed_document(
            repository_root=tmp_path,
            template_text=template,
            bindings=[Binding("INPUT", "input.txt")],
            output_relative_path="out.md",
        )

    assert excinfo.value.code == "OUTPUT_DIRECTORY_FSYNC_FAILED"
    assert (tmp_path / "out.md").exists()
    assert "INPUT" in (tmp_path / "out.md").read_text(encoding="utf-8")
    assert _stray_temp_files(tmp_path, "out.md") == []


# ---------------------------------------------------------------------------
# Adversarial tests: close-failure precedence
# ---------------------------------------------------------------------------
#
# Every ``os.close`` call in the module is routed through one of two governed helpers, chosen at
# each call site by construction: ``_close_or_raise`` on an otherwise-successful path (no other
# error already in flight), where a close failure is itself the sole reportable event; and
# ``_close_best_effort`` wherever a primary error is already being constructed or is already
# propagating, where a close failure must never replace, chain over, or otherwise mask that
# primary error. The two tests below exercise both branches of that precedence directly on the
# retained temporary publication file descriptor, which the module closes explicitly (not via
# ``finally``) once after a successful write+fsync+``fclonefileat`` clone (the otherwise-
# successful case) and, on a separate path, discards only as best-effort cleanup while a write
# failure is already the primary error (the already-failing case).


def _patch_open_to_capture_private_temp_fd(monkeypatch: pytest.MonkeyPatch) -> dict[str, object]:
    """Capture the fd returned for the private temporary output file's own ``os.open`` call.

    Identifying the target descriptor by its own creation call (rather than by call-order across
    the whole run, which also opens the repository root, bound inputs, and output-parent
    directories) keeps the injected failure bound to exactly the one descriptor under test.
    """

    real_open = module.os.open
    state: dict[str, object] = {"temp_fd": None}

    def fake_open(path, flags, mode=0o777, *, dir_fd=None):  # type: ignore[no-untyped-def]
        fd = real_open(path, flags, mode, dir_fd=dir_fd)
        if (
            isinstance(path, str)
            and path.endswith(module._TEMP_FILE_SUFFIX)
            and (flags & os.O_CREAT)
            and (flags & os.O_EXCL)
        ):
            state["temp_fd"] = fd
        return fd

    monkeypatch.setattr(module.os, "open", fake_open)
    return state


def test_close_failure_on_an_otherwise_successful_path_becomes_the_governed_error(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """A close failure with no other error in flight is itself the sole reportable event.

    The retained temporary publication descriptor is closed, by descriptor value, exactly once
    after the publishing ``fclonefileat`` clone has already succeeded -- an otherwise-fully-
    successful path all the way through durable publication. Failing only that one close call
    must convert into a stable ``GovernanceHashBoundDocumentError`` instead of letting a raw,
    unguarded ``OSError`` (and any interpreter traceback) escape. Because the clone has already
    made the document durably visible under its final name by the time this close is attempted,
    the already-published file is never rolled back on account of this cleanup-only failure --
    identical in spirit to the already-covered directory-fsync-after-successful-publish case.
    """

    _write(tmp_path, "input.txt", b"payload")
    template = f"{PLACEHOLDER}\n"

    state = _patch_open_to_capture_private_temp_fd(monkeypatch)
    real_close = module.os.close

    def fake_close(fd: int) -> None:
        if state["temp_fd"] is not None and fd == state["temp_fd"]:
            state["temp_fd"] = None  # fail exactly once, at the targeted descriptor
            raise OSError(5, "simulated close failure on an otherwise-successful path")
        return real_close(fd)

    monkeypatch.setattr(module.os, "close", fake_close)

    with pytest.raises(GovernanceHashBoundDocumentError) as excinfo:
        module.write_governed_document(
            repository_root=tmp_path,
            template_text=template,
            bindings=[Binding("INPUT", "input.txt")],
            output_relative_path="out.md",
        )

    assert excinfo.value.code == "OUTPUT_TEMP_CLOSE_FAILED"
    assert isinstance(excinfo.value.__cause__, OSError)
    assert (tmp_path / "out.md").exists()
    assert "INPUT" in (tmp_path / "out.md").read_text(encoding="utf-8")
    assert _stray_temp_files(tmp_path, "out.md") == []


def test_close_failure_on_an_already_failing_path_never_masks_the_primary_error(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """A close failure while a primary error is already in flight must never replace it.

    The private temporary output file's write is made to fail first (the primary, already-active
    error), and the module's own best-effort close of that same descriptor -- performed only as
    cleanup after the write has already failed -- is also made to fail. The call must still raise
    exactly the original write-failure code; the close failure must be silently discarded rather
    than surfacing as its own error, replacing the primary error's code, or escaping as an
    unguarded traceback.
    """

    _write(tmp_path, "input.txt", b"payload")
    template = f"{PLACEHOLDER}\n"

    state = _patch_open_to_capture_private_temp_fd(monkeypatch)

    def failing_write(_fd: int, _data: bytes) -> int:
        raise OSError(28, "simulated disk-full write failure")

    monkeypatch.setattr(module.os, "write", failing_write)

    real_close = module.os.close

    def fake_close(fd: int) -> None:
        if state["temp_fd"] is not None and fd == state["temp_fd"]:
            state["temp_fd"] = None  # fail exactly once, at the targeted descriptor
            raise OSError(5, "simulated close failure while a primary error is already active")
        return real_close(fd)

    monkeypatch.setattr(module.os, "close", fake_close)

    with pytest.raises(GovernanceHashBoundDocumentError) as excinfo:
        module.write_governed_document(
            repository_root=tmp_path,
            template_text=template,
            bindings=[Binding("INPUT", "input.txt")],
            output_relative_path="out.md",
        )

    assert excinfo.value.code == "OUTPUT_TEMP_WRITE_FAILED"
    assert isinstance(excinfo.value.__cause__, OSError)
    assert excinfo.value.__cause__.errno == 28
    assert not (tmp_path / "out.md").exists()
    assert _stray_temp_files(tmp_path, "out.md") == []
