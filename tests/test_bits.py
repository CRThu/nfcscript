"""BITS_UPDATE / BITS_SET / BITS_RESET 测试"""
import pytest
from nfc.bits import BITS_UPDATE, BITS_SET, BITS_RESET


class TestBITS_UPDATE:

    def test_replace_bits(self):
        result = BITS_UPDATE(0b1010_0000, 0b0011_0000, 0b0010_0000)
        assert result == 0b1010_0000

    def test_clear_and_set(self):
        result = BITS_UPDATE(0b1111_0000, 0b0000_1111, 0b0000_1010)
        assert result == 0b1111_1010

    def test_no_change(self):
        result = BITS_UPDATE(0b1100_1100, 0b0011_0000, 0b0000_0000)
        assert result == 0b1100_1100

    def test_set_all_mask_bits(self):
        result = BITS_UPDATE(0x00, 0xFF, 0xFF)
        assert result == 0xFF

    def test_clear_all_mask_bits(self):
        result = BITS_UPDATE(0xFF, 0xFF, 0x00)
        assert result == 0x00

    def test_data_outside_mask_raises(self):
        with pytest.raises(AssertionError, match="bits outside mask"):
            BITS_UPDATE(0x00, 0x0F, 0xF0)


class TestBITS_SET:

    def test_set_single_bit(self):
        assert BITS_SET(0x00, 0x01) == 0x01

    def test_set_multiple_bits(self):
        assert BITS_SET(0x00, 0x0F) == 0x0F

    def test_already_set(self):
        assert BITS_SET(0xFF, 0x0F) == 0xFF

    def test_set_zero_mask(self):
        assert BITS_SET(0xAB, 0x00) == 0xAB

    def test_set_high_bit(self):
        assert BITS_SET(0x00, 0x80) == 0x80


class TestBITS_RESET:

    def test_reset_single_bit(self):
        assert BITS_RESET(0xFF, 0x01) == 0xFE

    def test_reset_multiple_bits(self):
        assert BITS_RESET(0xFF, 0x0F) == 0xF0

    def test_already_cleared(self):
        assert BITS_RESET(0x00, 0x0F) == 0x00

    def test_reset_zero_mask(self):
        assert BITS_RESET(0xAB, 0x00) == 0xAB

    def test_reset_all(self):
        assert BITS_RESET(0xFF, 0xFF) == 0x00

    def test_reset_high_bits(self):
        assert BITS_RESET(0xFF, 0xF0) == 0x0F
