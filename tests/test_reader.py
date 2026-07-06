"""reader 模块测试 (connect / get_reader / active / transceive / session 等)"""
import pytest
from unittest.mock import MagicMock, patch, PropertyMock
from nfc import reader
from nfctester.drivers.card_reader import CardInfo, TransceiveBits


@pytest.fixture(autouse=True)
def reset_state():
    """每个测试前重置全局状态"""
    reader._state._reader = None
    reader._state._connected = False
    yield
    reader._state._reader = None
    reader._state._connected = False


def _mock_reader():
    mock = MagicMock()
    mock.transceive.return_value = TransceiveBits(data=[0xAA, 0xBB], bits=8)
    mock.active.return_value = CardInfo(uid=[0x01, 0x02, 0x03, 0x04], atq=[0x44, 0x00], sak=0x00)
    return mock


class TestConnect:

    @patch.object(reader.CardReaderRegistry, "create")
    def test_connect_with_params(self, mock_create):
        mock_reader = _mock_reader()
        mock_create.return_value = mock_reader
        reader.connect(port="COM99", reader_type="pn532")
        mock_create.assert_called_once_with("pn532", transport="serial", port="COM99")
        mock_reader.open.assert_called_once()
        assert reader._state._connected is True

    @patch.object(reader.CardReaderRegistry, "create")
    def test_connect_from_env(self, mock_create, monkeypatch):
        monkeypatch.setenv("NFC_PORT", "COM10")
        monkeypatch.setenv("NFC_READER", "pn532")
        mock_create.return_value = _mock_reader()
        reader.connect()
        mock_create.assert_called_once_with("pn532", transport="serial", port="COM10")

    def test_connect_no_port_raises(self):
        with pytest.raises(ValueError, match="未指定串口"):
            reader.connect(reader_type="pn532")

    def test_connect_no_reader_type_raises(self):
        with pytest.raises(ValueError, match="未指定读卡器类型"):
            reader.connect(port="COM99")

    @patch.object(reader.CardReaderRegistry, "create")
    def test_connect_overrides_env(self, mock_create, monkeypatch):
        monkeypatch.setenv("NFC_PORT", "COM10")
        monkeypatch.setenv("NFC_READER", "clrc663")
        mock_create.return_value = _mock_reader()
        reader.connect(port="COM99", reader_type="pn532")
        mock_create.assert_called_once_with("pn532", transport="serial", port="COM99")


class TestGetReader:

    def test_get_reader_when_connected(self):
        mock = _mock_reader()
        reader._state._reader = mock
        reader._state._connected = True
        assert reader.get_reader() is mock

    def test_get_reader_when_not_connected(self):
        with pytest.raises(AssertionError):
            reader.get_reader()


class TestTransceive:

    def test_transceive_returns_data(self):
        mock = _mock_reader()
        reader._state._reader = mock
        reader._state._connected = True
        result = reader.transceive([0x30, 0x00])
        assert result == [0xAA, 0xBB]
        mock.transceive.assert_called_once_with([0x30, 0x00], tx_crc=True, rx_crc=True)

    def test_transceive_no_crc(self):
        mock = _mock_reader()
        reader._state._reader = mock
        reader._state._connected = True
        reader.transceive([0x30], tx_crc=False, rx_crc=False)
        mock.transceive.assert_called_once_with([0x30], tx_crc=False, rx_crc=False)

    def test_transceive_empty_result(self):
        mock = _mock_reader()
        mock.transceive.return_value = None
        reader._state._reader = mock
        reader._state._connected = True
        result = reader.transceive([0x30])
        assert result == []

    def test_transceive_not_connected(self):
        with pytest.raises(AssertionError):
            reader.transceive([0x30])


class TestTransceiveBits:

    def test_transceive_bits_returns_result(self):
        mock = _mock_reader()
        reader._state._reader = mock
        reader._state._connected = True
        result = reader.transceive_bits([0x26], last_tx_bits=7, tx_crc=False, rx_crc=False)
        assert result is not None
        assert result.data == [0xAA, 0xBB]

    def test_transceive_bits_passes_params(self):
        mock = _mock_reader()
        reader._state._reader = mock
        reader._state._connected = True
        reader.transceive_bits([0x26], last_tx_bits=7, tx_crc=False, rx_crc=False)
        mock.transceive.assert_called_once_with([0x26], last_tx_bits=7, tx_crc=False, rx_crc=False)


class TestReqa:

    @patch.object(reader, "transceive_bits")
    def test_reqa_default(self, mock_tb):
        mock_tb.return_value = TransceiveBits(data=[0x44, 0x00], bits=8)
        result = reader.reqa()
        mock_tb.assert_called_once_with([0x26], last_tx_bits=7, tx_crc=False, rx_crc=False)
        assert result is not None

    @patch.object(reader, "transceive_bits")
    def test_reqa_custom_cmd(self, mock_tb):
        mock_tb.return_value = TransceiveBits(data=[0x44, 0x00], bits=8)
        reader.reqa(cmd=0x20)
        mock_tb.assert_called_once_with([0x20], last_tx_bits=7, tx_crc=False, rx_crc=False)


class TestWupa:

    @patch.object(reader, "transceive_bits")
    def test_wupa(self, mock_tb):
        mock_tb.return_value = TransceiveBits(data=[0x44, 0x00], bits=8)
        result = reader.wupa()
        mock_tb.assert_called_once_with([0x52], last_tx_bits=7, tx_crc=False, rx_crc=False)
        assert result is not None


class TestHalt:

    @patch.object(reader, "transceive")
    def test_halt(self, mock_ts):
        mock_ts.return_value = []
        result = reader.halt()
        mock_ts.assert_called_once_with([0x50, 0x00], tx_crc=True, rx_crc=True)


class TestSelect:

    @patch.object(reader, "transceive")
    def test_select_cl1(self, mock_ts):
        mock_ts.return_value = [0x08]
        result = reader.select(cl_level=1, uid=[0x04, 0x12, 0x34, 0x56, 0x61])
        mock_ts.assert_called_once_with(
            [0x93, 0x70, 0x04, 0x12, 0x34, 0x56, 0x61],
            tx_crc=True, rx_crc=True
        )
        assert result == [0x08]

    @patch.object(reader, "transceive")
    def test_select_cl2(self, mock_ts):
        mock_ts.return_value = [0x08]
        reader.select(cl_level=2, uid=[0x04, 0x12, 0x34, 0x56, 0x61])
        mock_ts.assert_called_once_with(
            [0x95, 0x70, 0x04, 0x12, 0x34, 0x56, 0x61],
            tx_crc=True, rx_crc=True
        )

    @patch.object(reader, "transceive")
    def test_select_cl3(self, mock_ts):
        mock_ts.return_value = [0x08]
        reader.select(cl_level=3, uid=[0x04, 0x12, 0x34, 0x56, 0x61])
        mock_ts.assert_called_once_with(
            [0x97, 0x70, 0x04, 0x12, 0x34, 0x56, 0x61],
            tx_crc=True, rx_crc=True
        )

    def test_select_invalid_cl(self):
        with pytest.raises(ValueError, match="Invalid CL level"):
            reader.select(cl_level=4, uid=[0x04, 0x12, 0x34, 0x56, 0x61])


class TestAnticoll:

    @patch.object(reader, "transceive_bits")
    def test_anticoll_cl1(self, mock_tb):
        mock_tb.return_value = TransceiveBits(data=[0x04, 0x12, 0x34, 0x56, 0x61], bits=40)
        result = reader.anticoll(cl_level=1)
        mock_tb.assert_called_once_with([0x93, 0x20], last_tx_bits=0, tx_crc=False, rx_crc=False)
        assert result is not None

    @patch.object(reader, "transceive_bits")
    def test_anticoll_cl2(self, mock_tb):
        mock_tb.return_value = TransceiveBits(data=[0x04, 0x12, 0x34, 0x56, 0x61], bits=40)
        reader.anticoll(cl_level=2)
        mock_tb.assert_called_once_with([0x95, 0x20], last_tx_bits=0, tx_crc=False, rx_crc=False)

    @patch.object(reader, "transceive_bits")
    def test_anticoll_with_uid_prefix(self, mock_tb):
        mock_tb.return_value = TransceiveBits(data=[0x04, 0x12, 0x34, 0x56, 0x61], bits=40)
        reader.anticoll(cl_level=1, uid_prefix=[0x04, 0x12, 0x34, 0x56])
        mock_tb.assert_called_once_with(
            [0x93, 0x20, 0x04, 0x12, 0x34, 0x56],
            last_tx_bits=0, tx_crc=False, rx_crc=False
        )


class TestFieldControl:

    def test_field_on(self):
        mock = _mock_reader()
        reader._state._reader = mock
        reader._state._connected = True
        reader.field_on()
        assert mock.rf_field is True

    def test_field_off(self):
        mock = _mock_reader()
        reader._state._reader = mock
        reader._state._connected = True
        reader.field_off()
        assert mock.rf_field is False


class TestSession:

    @patch.object(reader._state, "disconnect")
    @patch.object(reader._state, "connect")
    def test_session_yields_reader(self, mock_connect, mock_disconnect):
        mock_rdr = _mock_reader()

        def fake_connect(port="COM20", reader_type="pn532"):
            reader._state._reader = mock_rdr
            reader._state._connected = True

        mock_connect.side_effect = fake_connect

        with reader.session(port="COM99", reader_type="pn532") as r:
            assert r is mock_rdr
        mock_disconnect.assert_called_once()

    def test_session_no_port_raises(self):
        with pytest.raises(ValueError, match="未指定串口"):
            with reader.session(reader_type="pn532"):
                pass

    def test_session_no_reader_type_raises(self):
        with pytest.raises(ValueError, match="未指定读卡器类型"):
            with reader.session(port="COM99"):
                pass


class TestGetSelCmd:

    def test_cl1(self):
        assert reader._get_sel_cmd(1) == 0x93

    def test_cl2(self):
        assert reader._get_sel_cmd(2) == 0x95

    def test_cl3(self):
        assert reader._get_sel_cmd(3) == 0x97

    def test_invalid(self):
        with pytest.raises(ValueError):
            reader._get_sel_cmd(4)
