#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Tests for the coptictranslit command-line interface."""

import io

import pytest

from coptictranslit.__main__ import main


def test_file_to_stdout(tmp_path, capsys):
    src = tmp_path / "in.txt"
    src.write_text("ⲡⲛⲟⲩⲧⲉ", encoding="utf-8")
    assert main([str(src)]) == 0
    assert capsys.readouterr().out.strip() == "pnoute"


def test_file_to_output_file(tmp_path):
    src = tmp_path / "in.txt"
    dst = tmp_path / "out.txt"
    src.write_text("ⲙⲁⲣⲓⲁ ⲡⲛⲟⲩⲧⲉ", encoding="utf-8")
    assert main([str(src), "-o", str(dst)]) == 0
    assert dst.read_text(encoding="utf-8") == "maria pnoute"


def test_stdin(monkeypatch, capsys):
    monkeypatch.setattr("sys.stdin", io.StringIO("ⲁⲅⲁⲡⲏ"))
    assert main([]) == 0
    assert capsys.readouterr().out.strip() == "aghape"


def test_unmapped_warning_goes_to_stderr(tmp_path, capsys):
    src = tmp_path / "in.txt"
    src.write_text("ⲡⲛⲟⲩⲧⲉ ⳁ", encoding="utf-8")
    assert main([str(src)]) == 0
    captured = capsys.readouterr()
    assert "ⳁ" in captured.err
    assert "pnoute" in captured.out


def test_version_flag(capsys):
    with pytest.raises(SystemExit) as exc:
        main(["--version"])
    assert exc.value.code == 0
    assert "coptictranslit" in capsys.readouterr().out
