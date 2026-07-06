"""PARSE_HEX / FORMAT_HEX 测试"""
import pytest
from nfc.hex_util import PARSE_HEX, FORMAT_HEX


class TestPARSE_HEX:

    def test_simple_hex(self):
        assert PARSE_HEX("AA BB CC") == ("AABBCC", 0)

    def test_bit_mark(self):
        hex_str, bits = PARSE_HEX("AA BB 7'h03")
        assert hex_str == "AABB03"
        assert bits == 7

    def test_single_byte_two_digits(self):
        hex_str, bits = PARSE_HEX("4'h0C")
        assert hex_str == "0C"
        assert bits == 4

    def test_single_byte_odd_hex_padded(self):
        hex_str, bits = PARSE_HEX("4'hC")
        assert hex_str == "0C"
        assert bits == 4

    def test_single_byte_odd_hex_a(self):
        hex_str, bits = PARSE_HEX("7'h3")
        assert hex_str == "03"
        assert bits == 7

    def test_no_space(self):
        assert PARSE_HEX("AABBCC") == ("AABBCC", 0)

    def test_empty_string(self):
        assert PARSE_HEX("") == ("", 0)

    def test_whitespace_only(self):
        assert PARSE_HEX("   ") == ("", 0)

    def test_multiple_bit_marks_all_replaced(self):
        hex_str, bits = PARSE_HEX("7'h03 AA 4'hC")
        assert hex_str == "03AA0C"
        assert bits == 4

    def test_multiple_bit_marks_first_and_last(self):
        hex_str, bits = PARSE_HEX("4'hA BB 7'h03")
        assert hex_str == "0ABB03"
        assert bits == 7

    def test_three_bit_marks(self):
        hex_str, bits = PARSE_HEX("4'h1 4'h2 4'h3")
        assert hex_str == "010203"
        assert bits == 4

    def test_invalid_hex_raises(self):
        with pytest.raises(ValueError, match="不合法的十六进制数据"):
            PARSE_HEX("ZZZZ")

    def test_odd_hex_digits_raises(self):
        with pytest.raises(ValueError):
            PARSE_HEX("ABC")

    def test_hex_with_uppercase(self):
        assert PARSE_HEX("FF AA") == ("FFAA", 0)

    def test_hex_with_lowercase(self):
        assert PARSE_HEX("ff aa") == ("ffaa", 0)

    def test_bit_mark_no_space_around(self):
        hex_str, bits = PARSE_HEX("AA7'h03BB")
        assert hex_str == "AA03BB"
        assert bits == 7

    def test_bit_mark_only(self):
        hex_str, bits = PARSE_HEX("8'hFF")
        assert hex_str == "FF"
        assert bits == 8

    def test_bit_mark_with_lower_hex(self):
        hex_str, bits = PARSE_HEX("7'h0a")
        assert hex_str == "0a"
        assert bits == 7

    def test_roundtrip_with_format(self):
        data = [0xAA, 0xBB, 0x03]
        formatted = FORMAT_HEX(data, 7)
        parsed, bits = PARSE_HEX(formatted)
        assert bits == 7
        assert bytes.fromhex(parsed) == bytes(data)

    def test_roundtrip_single_byte(self):
        formatted = FORMAT_HEX(0xFF, 4)
        parsed, bits = PARSE_HEX(formatted)
        assert bits == 4
        assert parsed == "FF"

    def test_roundtrip_no_bits(self):
        formatted = FORMAT_HEX([0x01, 0x02, 0x03])
        parsed, bits = PARSE_HEX(formatted)
        assert bits == 0
        assert parsed == "010203"


class TestFORMAT_HEX:

    def test_int_no_bits(self):
        assert FORMAT_HEX(0xAABBCC) == "AA BB CC"

    def test_int_with_bits(self):
        assert FORMAT_HEX(0xAABB03, 7) == "AA BB 7'h03"

    def test_int_single_byte_bits(self):
        assert FORMAT_HEX(0xFF, 4) == "4'hFF"

    def test_bytes_no_bits(self):
        assert FORMAT_HEX(b'\xAA\xBB\xCC') == "AA BB CC"

    def test_bytes_with_bits(self):
        assert FORMAT_HEX(b'\xAA\xBB\x03', 7) == "AA BB 7'h03"

    def test_list_no_bits(self):
        assert FORMAT_HEX([0xAA, 0xBB, 0xCC]) == "AA BB CC"

    def test_list_with_bits(self):
        assert FORMAT_HEX([0xAA, 0xBB, 0x03], 7) == "AA BB 7'h03"

    def test_str_no_bits(self):
        assert FORMAT_HEX("AABBCC") == "AA BB CC"

    def test_str_with_bits(self):
        assert FORMAT_HEX("AABB03", 7) == "AA BB 7'h03"

    def test_empty_string(self):
        assert FORMAT_HEX("") == ""

    def test_empty_bytes(self):
        assert FORMAT_HEX(b'') == ""

    def test_empty_list(self):
        assert FORMAT_HEX([]) == ""

    def test_unsupported_type(self):
        with pytest.raises(TypeError, match="不支持的输入类型"):
            FORMAT_HEX(3.14)

    def test_hex_str_with_spaces(self):
        assert FORMAT_HEX("AA BB CC") == "AA BB CC"

    def test_lowercase_int(self):
        assert FORMAT_HEX(0xff) == "FF"

    def test_int_zero(self):
        assert FORMAT_HEX(0) == "00"

    def test_bytes_single(self):
        assert FORMAT_HEX(b'\xFF') == "FF"

    def test_list_single(self):
        assert FORMAT_HEX([0xFF]) == "FF"

    def test_int_large(self):
        assert FORMAT_HEX(0xAABBCCDD) == "AA BB CC DD"

    def test_bits_1(self):
        assert FORMAT_HEX(0x01, 1) == "1'h01"

    def test_bits_7(self):
        assert FORMAT_HEX(0x26, 7) == "7'h26"
