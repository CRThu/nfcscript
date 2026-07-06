"""GET_BCC 测试"""
import pytest
from nfc.checksum import GET_BCC


class TestGET_BCC:

    def test_all_zero(self):
        assert GET_BCC([0x00, 0x00, 0x00, 0x00]) == 0x00

    def test_simple(self):
        assert GET_BCC([0x01, 0x02, 0x03, 0x04]) == 0x01 ^ 0x02 ^ 0x03 ^ 0x04

    def test_all_ff(self):
        assert GET_BCC([0xFF, 0xFF, 0xFF, 0xFF]) == 0x00

    def test_known_uid(self):
        uid = [0x04, 0x12, 0x34, 0x56]
        expected = 0x04 ^ 0x12 ^ 0x34 ^ 0x56
        assert GET_BCC(uid) == expected

    def test_wrong_length_raises(self):
        with pytest.raises(AssertionError):
            GET_BCC([0x01, 0x02, 0x03])

    def test_too_long_raises(self):
        with pytest.raises(AssertionError):
            GET_BCC([0x01, 0x02, 0x03, 0x04, 0x05])

    def test_empty_raises(self):
        with pytest.raises(AssertionError):
            GET_BCC([])
