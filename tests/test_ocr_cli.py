import argparse

import pytest

import ocr
from conftest import PAGE_TEXTS


def test_parse_variable():
    assert ocr.parse_variable("tessedit_char_whitelist=ABC=1") == (
        "tessedit_char_whitelist",
        "ABC=1",
    )


@pytest.mark.parametrize("value", ["novalue", "=value"])
def test_parse_variable_rejects_bad_input(value):
    with pytest.raises(argparse.ArgumentTypeError):
        ocr.parse_variable(value)


def test_help(capsys):
    with pytest.raises(SystemExit) as exc:
        ocr.main(["--help"])
    assert exc.value.code == 0
    assert "--grayscale" in capsys.readouterr().out


def test_missing_file(tmp_path, capsys):
    with pytest.raises(SystemExit) as exc:
        ocr.main([str(tmp_path / "missing.pdf")])
    assert exc.value.code == 2
    assert "no such file" in capsys.readouterr().err


def test_invalid_psm(capsys):
    with pytest.raises(SystemExit) as exc:
        ocr.main(["--psm", "99", "x.pdf"])
    assert exc.value.code == 2


@pytest.mark.integration
def test_prints_text_to_stdout(sample_pdf, capsys):
    ocr.main(["--grayscale", str(sample_pdf)])
    lines = [line for line in capsys.readouterr().out.splitlines() if line.strip()]
    assert lines == PAGE_TEXTS


@pytest.mark.integration
def test_writes_output_dir(sample_pdf, tmp_path):
    out = tmp_path / "out"
    ocr.main(["--psm", "6", "--first-page", "2", "-o", str(out), str(sample_pdf)])
    assert (out / "sample.txt").read_text().strip() == PAGE_TEXTS[1]
