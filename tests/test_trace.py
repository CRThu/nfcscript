"""trace 模块测试"""
from unittest.mock import patch, MagicMock
from nfc import trace


class TestSetLayer:

    @patch("nfc.trace._trace")
    def test_set_layer_enable(self, mock_trace):
        trace.set_layer("DRIVER", True)
        mock_trace.set_layer.assert_called_once_with("DRIVER", True)

    @patch("nfc.trace._trace")
    def test_set_layer_disable(self, mock_trace):
        trace.set_layer("PROTOCOL", False)
        mock_trace.set_layer.assert_called_once_with("PROTOCOL", False)

    @patch("nfc.trace._trace")
    def test_set_layer_default_enable(self, mock_trace):
        trace.set_layer("DRIVER")
        mock_trace.set_layer.assert_called_once_with("DRIVER", True)


class TestSetLevel:

    @patch("nfc.trace._trace")
    def test_set_level(self, mock_trace):
        trace.set_level("DEBUG")
        mock_trace.set_level.assert_called_once_with("DEBUG")


class TestSetParse:

    @patch("nfc.trace._trace")
    def test_set_parse(self, mock_trace):
        trace.set_parse(2)
        mock_trace.set_parse.assert_called_once_with(2)


class TestSetCardType:

    @patch("nfc.trace._trace")
    def test_set_card_type(self, mock_trace):
        trace.set_card_type("mifare_classic_1k")
        mock_trace.set_card_type.assert_called_once_with("mifare_classic_1k")


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
    def test_success(self, mock_trace):
        trace.success("ok message")
        mock_trace.success.assert_called_once_with("ok message")

    @patch("nfc.trace._trace")
    def test_debug(self, mock_trace):
        trace.debug("debug message")
        mock_trace.debug.assert_called_once_with("debug message")
