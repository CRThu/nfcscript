"""trace 模块测试"""
from unittest.mock import patch, MagicMock
from nfc import trace


class TestSetParse:

    @patch("nfc.trace._trace")
    def test_set_parse(self, mock_trace):
        trace.set_parse(2)
        mock_trace.set_parse.assert_called_once_with(2)


class TestLogFunctions:

    @patch("nfc.trace._trace")
    def test_info(self, mock_trace):
        trace.info("test message")
        mock_trace.info.assert_called_once_with("test message")

    @patch("nfc.trace._trace")
    def test_error(self, mock_trace):
        trace.error("error message")
        mock_trace.error.assert_called_once_with("error message")

    @patch("nfc.trace._trace")
    def test_warning(self, mock_trace):
        trace.warning("warn message")
        mock_trace.warning.assert_called_once_with("warn message")

    @patch("nfc.trace._trace")
    def test_debug(self, mock_trace):
        trace.debug("debug message")
        mock_trace.debug.assert_called_once_with("debug message")

    @patch("nfc.trace._trace")
    def test_app(self, mock_trace):
        trace.app("app message")
        mock_trace.app.assert_called_once_with("app message")

    @patch("nfc.trace._trace")
    def test_log(self, mock_trace):
        trace.log("log message", layer="debug")
        mock_trace.log.assert_called_once_with("log message", "debug")
