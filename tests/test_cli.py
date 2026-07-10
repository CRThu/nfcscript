"""cli 模块测试 (_find_dotenv_all / run_script)"""
import os
import pytest
from unittest.mock import patch, MagicMock
from nfc.cli import _find_dotenv_all


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
