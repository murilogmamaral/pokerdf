"""Unit tests for the command line helpers of main."""

import os
from pathlib import Path

import pytest

from pokerdf.main import (
    _build_parser,
    _create_destination_folder,
    _print_elapsed_time,
    _validate_source_directory,
)
import datetime


# ---------------------------------------------------------------------------
# _build_parser
# ---------------------------------------------------------------------------
def test_parser_reads_the_convert_command() -> None:
    arguments = _build_parser().parse_args(["convert", "/tmp/hands"])

    assert arguments.command == "convert"
    assert arguments.path == "/tmp/hands"


def test_parser_defaults_modeling_to_no_anonymization() -> None:
    arguments = _build_parser().parse_args(["modeling", "/tmp/parquets"])

    assert arguments.gdpr is None
    assert arguments.salt is None


def test_parser_reads_the_gdpr_arguments() -> None:
    arguments = _build_parser().parse_args(
        ["modeling", "/tmp/parquets", "--gdpr", "full", "--salt", "secret"]
    )

    assert arguments.gdpr == "full"
    assert arguments.salt == "secret"


def test_parser_reads_the_keep_owner_mode() -> None:
    arguments = _build_parser().parse_args(
        ["modeling", "/tmp/parquets", "--gdpr", "keep-owner"]
    )

    assert arguments.gdpr == "keep-owner"


def test_parser_rejects_an_unknown_gdpr_mode() -> None:
    with pytest.raises(SystemExit):
        _build_parser().parse_args(["modeling", "/tmp/parquets", "--gdpr", "rgpd"])


def test_parser_rejects_an_unknown_command() -> None:
    with pytest.raises(SystemExit):
        _build_parser().parse_args(["modelling", "/tmp/parquets"])


def test_parser_requires_a_command() -> None:
    with pytest.raises(SystemExit):
        _build_parser().parse_args([])


# ---------------------------------------------------------------------------
# _validate_source_directory
# ---------------------------------------------------------------------------
def test_validate_source_directory_accepts_a_valid_directory(tmp_path: Path) -> None:
    (tmp_path / "HH20200607 T111.txt").touch()
    # Must not raise nor exit
    _validate_source_directory(str(tmp_path), ".txt", "poker hand history files")


def test_validate_source_directory_rejects_missing_path(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    with pytest.raises(SystemExit):
        _validate_source_directory(str(tmp_path / "missing"), ".txt", "files")
    assert "does not exist" in capsys.readouterr().out


def test_validate_source_directory_rejects_a_file(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    file_path = tmp_path / "HH20200607 T111.txt"
    file_path.touch()
    with pytest.raises(SystemExit):
        _validate_source_directory(str(file_path), ".txt", "files")
    assert "is not a directory" in capsys.readouterr().out


def test_validate_source_directory_rejects_an_empty_directory(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    with pytest.raises(SystemExit):
        _validate_source_directory(str(tmp_path), ".txt", "files")
    assert "is empty" in capsys.readouterr().out


def test_validate_source_directory_rejects_wrong_content(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    (tmp_path / "notes.md").touch()
    with pytest.raises(SystemExit):
        _validate_source_directory(str(tmp_path), ".txt", "poker hand history files")
    assert "does not contain any poker hand history files" in capsys.readouterr().out


# ---------------------------------------------------------------------------
# _create_destination_folder
# ---------------------------------------------------------------------------
def test_create_destination_folder_creates_a_session_folder(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.chdir(tmp_path)

    destination = _create_destination_folder("output")

    assert destination.startswith("./output/")
    assert os.path.isdir(destination)


# ---------------------------------------------------------------------------
# _print_elapsed_time
# ---------------------------------------------------------------------------
def test_print_elapsed_time_reports_a_readable_message(
    capsys: pytest.CaptureFixture[str],
) -> None:
    start_time = datetime.datetime.now() - datetime.timedelta(hours=1, minutes=2)

    _print_elapsed_time(start_time)

    out = capsys.readouterr().out
    assert "Processing completed in 1 hours, 2 minutes," in out
