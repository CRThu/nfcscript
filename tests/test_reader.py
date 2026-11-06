"""reader 模块测试 (connect / get_reader / active / transceive / session 等)"""
import os
import sys
import pytest
from unittest.mock import MagicMock, patch
import nfc
from nfc import reader
from nfctester.drivers.card_reader import CardInfo, TransceiveBits
from nfctester.registry import CardReaderRegistry


@pytest.fixture(autouse=True)
def reset_state():
    """每个测试前重置全局状态"""
    reader._target = None
    reader._connected = False
    yield
    reader._target = None
    reader._connected = False


def _mock_reader():
    mock = MagicMock()
    mock.transceive.return_value = TransceiveBits(data=[0xAA, 0xBB], bits=8)
    mock.active.return_value = CardInfo(uid=[0x01, 0x02, 0x03, 0x04], atq=[0x44, 0x00], sak=0x00)
    mock.rf_field = False
    mock.mf_crypto = False
    return mock


class TestConnect:

    @patch.object(CardReaderRegistry, "create")
    def test_connect_with_params(self, mock_create):
        mock_rdr = _mock_reader()
        mock_create.return_value = mock_rdr
        nfc.connect(port="COM99", reader_type="pn532")
        mock_create.assert_called_once_with("pn532", transport="serial", port="COM99")
        mock_rdr.open.assert_called_once()
        assert reader._connected is True

    @patch.object(CardReaderRegistry, "create")
    def test_connect_from_env(self, mock_create, monkeypatch):
        monkeypatch.setenv("NFC_PORT", "COM10")
        monkeypatch.setenv("NFC_READER", "pn532")
        mock_create.return_value = _mock_reader()
        nfc.connect()
        mock_create.assert_called_once_with("pn532", transport="serial", port="COM10")

    def test_connect_no_port_raises(self, monkeypatch):
        monkeypatch.delenv("NFC_PORT", raising=False)
        monkeypatch.delenv("NFC_READER", raising=False)
        with pytest.raises(ValueError, match="未指定串口"):
            nfc.connect(reader_type="pn532")

    def test_connect_no_reader_type_raises(self, monkeypatch):
        monkeypatch.delenv("NFC_PORT", raising=False)
        monkeypatch.delenv("NFC_READER", raising=False)
        with pytest.raises(ValueError, match="未指定读卡器类型"):
            nfc.connect(port="COM99")

    @patch.object(CardReaderRegistry, "create")
    def test_connect_overrides_env(self, mock_create, monkeypatch):
        monkeypatch.setenv("NFC_PORT", "COM10")
        monkeypatch.setenv("NFC_READER", "clrc663")
        mock_create.return_value = _mock_reader()
        nfc.connect(port="COM99", reader_type="pn532")
        mock_create.assert_called_once_with("pn532", transport="serial", port="COM99")


class TestGetReader:

    def test_get_reader_when_connected(self):
        mock = _mock_reader()
        reader._target = mock
        reader._connected = True
        assert nfc.get_reader() is mock
        assert reader.target is mock

    def test_get_reader_when_not_connected(self, monkeypatch):
        monkeypatch.delenv("NFC_PORT", raising=False)
        monkeypatch.delenv("NFC_READER", raising=False)
        with pytest.raises(AssertionError):
            nfc.get_reader()


class TestTransceive:

    def test_transceive_returns_data(self):
        mock = _mock_reader()
        reader._target = mock
        reader._connected = True
        result = nfc.transceive([0x30, 0x00])
        assert result == [0xAA, 0xBB]
        mock.transceive.assert_called_once_with([0x30, 0x00], tx_crc=True, rx_crc=True, timeout=0.5)

    def test_transceive_no_crc(self):
        mock = _mock_reader()
        reader._target = mock
        reader._connected = True
        nfc.transceive([0x30], tx_crc=False, rx_crc=False)
        mock.transceive.assert_called_once_with([0x30], tx_crc=False, rx_crc=False, timeout=0.5)

    def test_transceive_with_timeout(self):
        mock = _mock_reader()
        reader._target = mock
        reader._connected = True
        nfc.transceive([0x30], timeout=1.2)
        mock.transceive.assert_called_once_with([0x30], tx_crc=True, rx_crc=True, timeout=1.2)

    def test_transceive_empty_result(self):
        mock = _mock_reader()
        mock.transceive.return_value = None
        reader._target = mock
        reader._connected = True
        result = nfc.transceive([0x30])
        assert result == []

    def test_transceive_not_connected(self, monkeypatch):
        monkeypatch.delenv("NFC_PORT", raising=False)
        monkeypatch.delenv("NFC_READER", raising=False)
        with pytest.raises(AssertionError):
            nfc.transceive([0x30])


class TestTransceiveBits:

    def test_transceive_bits_returns_result(self):
        mock = _mock_reader()
        reader._target = mock
        reader._connected = True
        result = nfc.transceive_bits([0x26], last_tx_bits=7, tx_crc=False, rx_crc=False)
        assert result is not None
        assert result.data == [0xAA, 0xBB]

    def test_transceive_bits_passes_params(self):
        mock = _mock_reader()
        reader._target = mock
        reader._connected = True
        nfc.transceive_bits([0x26], last_tx_bits=7, tx_crc=False, rx_crc=False)
        mock.transceive.assert_called_once_with([0x26], last_tx_bits=7, tx_crc=False, rx_crc=False, timeout=0.5)


class TestReqa:

    @patch("nfc.reader.transceive_bits")
    def test_reqa_default(self, mock_tb):
        mock_tb.return_value = TransceiveBits(data=[0x44, 0x00], bits=8)
        result = nfc.reqa()
        mock_tb.assert_called_once_with([0x26], last_tx_bits=7, tx_crc=False, rx_crc=False)
        assert result is not None

    @patch("nfc.reader.transceive_bits")
    def test_reqa_custom_cmd(self, mock_tb):
        mock_tb.return_value = TransceiveBits(data=[0x44, 0x00], bits=8)
        nfc.reqa(cmd=0x20)
        mock_tb.assert_called_once_with([0x20], last_tx_bits=7, tx_crc=False, rx_crc=False)


class TestWupa:

    @patch("nfc.reader.transceive_bits")
    def test_wupa(self, mock_tb):
        mock_tb.return_value = TransceiveBits(data=[0x44, 0x00], bits=8)
        result = nfc.wupa()
        mock_tb.assert_called_once_with([0x52], last_tx_bits=7, tx_crc=False, rx_crc=False)
        assert result is not None


class TestHalt:

    @patch("nfc.reader.transceive")
    def test_halt(self, mock_ts):
        mock_ts.return_value = []
        result = nfc.halt()
        mock_ts.assert_called_once_with([0x50, 0x00], tx_crc=True, rx_crc=True)


class TestSelect:

    @patch("nfc.reader.transceive")
    def test_select_cl1(self, mock_ts):
        mock_ts.return_value = [0x08]
        result = nfc.select(cl_level=1, uid=[0x04, 0x12, 0x34, 0x56, 0x61])
        mock_ts.assert_called_once_with(
            [0x93, 0x70, 0x04, 0x12, 0x34, 0x56, 0x61],
            tx_crc=True, rx_crc=True
        )
        assert result == [0x08]

    @patch("nfc.reader.transceive")
    def test_select_cl2(self, mock_ts):
        mock_ts.return_value = [0x08]
        nfc.select(cl_level=2, uid=[0x04, 0x12, 0x34, 0x56, 0x61])
        mock_ts.assert_called_once_with(
            [0x95, 0x70, 0x04, 0x12, 0x34, 0x56, 0x61],
            tx_crc=True, rx_crc=True
        )

    @patch("nfc.reader.transceive")
    def test_select_cl3(self, mock_ts):
        mock_ts.return_value = [0x08]
        nfc.select(cl_level=3, uid=[0x04, 0x12, 0x34, 0x56, 0x61])
        mock_ts.assert_called_once_with(
            [0x97, 0x70, 0x04, 0x12, 0x34, 0x56, 0x61],
            tx_crc=True, rx_crc=True
        )

    def test_select_invalid_cl(self):
        with pytest.raises(ValueError, match="Invalid CL level"):
            nfc.select(cl_level=4, uid=[0x04, 0x12, 0x34, 0x56, 0x61])


class TestAnticoll:

    @patch("nfc.reader.transceive_bits")
    def test_anticoll_cl1(self, mock_tb):
        mock_tb.return_value = TransceiveBits(data=[0x04, 0x12, 0x34, 0x56, 0x61], bits=40)
        result = nfc.anticoll(cl_level=1)
        mock_tb.assert_called_once_with([0x93, 0x20], last_tx_bits=0, tx_crc=False, rx_crc=False)
        assert result is not None

    @patch("nfc.reader.transceive_bits")
    def test_anticoll_cl2(self, mock_tb):
        mock_tb.return_value = TransceiveBits(data=[0x04, 0x12, 0x34, 0x56, 0x61], bits=40)
        nfc.anticoll(cl_level=2)
        mock_tb.assert_called_once_with([0x95, 0x20], last_tx_bits=0, tx_crc=False, rx_crc=False)

    @patch("nfc.reader.transceive_bits")
    def test_anticoll_with_uid_prefix(self, mock_tb):
        mock_tb.return_value = TransceiveBits(data=[0x04, 0x12, 0x34, 0x56, 0x61], bits=40)
        nfc.anticoll(cl_level=1, uid_prefix=[0x04, 0x12, 0x34, 0x56])
        mock_tb.assert_called_once_with(
            [0x93, 0x20, 0x04, 0x12, 0x34, 0x56],
            last_tx_bits=0, tx_crc=False, rx_crc=False
        )


class TestFieldControl:

    def test_field_on(self):
        mock = _mock_reader()
        reader._target = mock
        reader._connected = True
        nfc.field_on()
        assert mock.rf_field is True

    def test_field_off(self):
        mock = _mock_reader()
        reader._target = mock
        reader._connected = True
        nfc.field_off()
        assert mock.rf_field is False


class TestSession:

    @patch("nfc.reader.disconnect")
    @patch("nfc.reader.connect")
    def test_session_yields_reader(self, mock_connect, mock_disconnect):
        mock_rdr = _mock_reader()

        def fake_connect(port="COM20", reader_type="pn532"):
            reader._target = mock_rdr
            reader._connected = True

        mock_connect.side_effect = fake_connect

        with nfc.session(port="COM99", reader_type="pn532") as r:
            assert r is reader
        mock_disconnect.assert_called_once()

    def test_session_no_port_raises(self, monkeypatch):
        monkeypatch.delenv("NFC_PORT", raising=False)
        monkeypatch.delenv("NFC_READER", raising=False)
        with pytest.raises(ValueError, match="未指定串口"):
            with nfc.session(reader_type="pn532"):
                pass

    def test_session_no_reader_type_raises(self, monkeypatch):
        monkeypatch.delenv("NFC_PORT", raising=False)
        monkeypatch.delenv("NFC_READER", raising=False)
        with pytest.raises(ValueError, match="未指定读卡器类型"):
            with nfc.session(port="COM99"):
                pass


class TestGetSelCmd:

    def test_cl1(self):
        from nfc.reader import _get_sel_cmd
        assert _get_sel_cmd(1) == 0x93

    def test_cl2(self):
        from nfc.reader import _get_sel_cmd
        assert _get_sel_cmd(2) == 0x95

    def test_cl3(self):
        from nfc.reader import _get_sel_cmd
        assert _get_sel_cmd(3) == 0x97

    def test_invalid(self):
        from nfc.reader import _get_sel_cmd
        with pytest.raises(ValueError):
            _get_sel_cmd(4)


class TestReaderSingletonProxy:

    @patch.object(CardReaderRegistry, "create")
    def test_reader_rf_property_and_lazy_connect(self, mock_create, monkeypatch):
        monkeypatch.setenv("NFC_PORT", "COM10")
        monkeypatch.setenv("NFC_READER", "pn532")
        mock_rdr = _mock_reader()
        mock_create.return_value = mock_rdr

        # reader.rf triggers auto-connect
        reader.rf = True
        assert mock_rdr.rf_field is True
        assert reader.rf is True
        assert reader.rf_field is True
        assert reader.mf_crypto is False

    @patch.object(CardReaderRegistry, "create")
    def test_reader_delegates_to_functions_and_target(self, mock_create, monkeypatch):
        monkeypatch.setenv("NFC_PORT", "COM10")
        monkeypatch.setenv("NFC_READER", "pn532")
        mock_rdr = _mock_reader()
        mock_create.return_value = mock_rdr

        # reader.active calls active()
        card = reader.active()
        assert card is not None
        assert card.uid == [0x01, 0x02, 0x03, 0x04]

        # reader.custom_method delegates to mock_rdr
        mock_rdr.custom_method = MagicMock(return_value="OK")
        assert reader.custom_method() == "OK"
