"""cli 模块测试 (_find_dotenv_all / _parse_level / run_script)"""
import os
import pytest
from unittest.mock import patch, MagicMock
from nfc.cli import _find_dotenv_all, _parse_level


class TestFindDotenvAll:

    def test_finds_dotenv_chain(self, tmp_path):
        child = tmp_path / "sub" / "deep"
        child.mkdir(parents=True)
        (tmp_path / ".env").write_text("ROOT=1")
        (tmp_path / "sub" / ".env").write_text("SUB=1")
        result = _find_dotenv_all(str(child))
        assert len(result) == 2
        assert result[0].endswith(".env")

    def test_no_dotenv(self, tmp_path):
        empty = tmp_path / "empty"
        empty.mkdir()
        result = _find_dotenv_all(str(empty))
        assert result == []

    def test_reverses_order(self, tmp_path):
        (tmp_path / ".env").write_text("A=1")
        sub = tmp_path / "sub"
        sub.mkdir()
        (sub / ".env").write_text("B=1")
        result = _find_dotenv_all(str(sub))
        assert len(result) == 2
        assert result[0].endswith(".env")
        assert result[1].endswith(".env")
        assert result[0] != result[1]


class TestParseLevel:

    def test_zero(self):
        assert _parse_level("0") == 0

    def test_false(self):
        assert _parse_level("false") == 0

    def test_off(self):
        assert _parse_level("off") == 0

    def test_one(self):
        assert _parse_level("1") == 1

    def test_simple(self):
        assert _parse_level("simple") == 1

    def test_summary(self):
        assert _parse_level("summary") == 1

    def test_two(self):
        assert _parse_level("2") == 2

    def test_full(self):
        assert _parse_level("full") == 2

    def test_tree(self):
        assert _parse_level("tree") == 2

    def test_case_insensitive(self):
        assert _parse_level("FULL") == 2
        assert _parse_level("False") == 0

    def test_unknown_falls_to_1(self):
        assert _parse_level("unknown") == 1

    def test_whitespace(self):
        assert _parse_level("  2  ") == 2


class TestRunScript:

    def test_runs_script(self, tmp_path):
        script = tmp_path / "test_script.py"
        script.write_text("import sys; sys.exit(0)")
        with patch("nfc.cli.runpy.run_path") as mock_run:
            from nfc.cli import run_script
            run_script(str(script))
            mock_run.assert_called_once()

    def test_script_not_found(self):
        from nfc.cli import run_script
        with pytest.raises(FileNotFoundError):
            run_script("/nonexistent/script.py")
