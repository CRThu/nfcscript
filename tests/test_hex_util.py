"""PARSE_HEX / PARSE_HEX_BITS / FORMAT_HEX 测试"""
import pytest
from nfc.hex_util import PARSE_HEX, PARSE_HEX_BITS, FORMAT_HEX


class TestPARSE_HEX:
    """PARSE_HEX: 纯 hex 解析，返回 list[int]"""

    def test_simple_hex(self):
        assert PARSE_HEX("AA BB CC") == [0xAA, 0xBB, 0xCC]

    def test_no_space(self):
        assert PARSE_HEX("AABBCC") == [0xAA, 0xBB, 0xCC]

    def test_empty_string(self):
        assert PARSE_HEX("") == []

    def test_whitespace_only(self):
        assert PARSE_HEX("   ") == []

    def test_single_byte(self):
        assert PARSE_HEX("FF") == [0xFF]

    def test_lowercase(self):
        assert PARSE_HEX("ff aa") == [0xFF, 0xAA]

    def test_invalid_hex_raises(self):
        with pytest.raises(ValueError, match="不合法的十六进制数据"):
            PARSE_HEX("ZZZZ")

    def test_odd_hex_digits_raises(self):
        with pytest.raises(ValueError):
            PARSE_HEX("ABC")


class TestPARSE_HEX_BITS:
    """PARSE_HEX_BITS: 返回 tuple[list[int], int]，支持位截断"""

    # --- 基础测试 ---

    def test_simple_hex(self):
        assert PARSE_HEX_BITS("AA BB CC") == ([0xAA, 0xBB, 0xCC], 0)

    def test_empty_string(self):
        assert PARSE_HEX_BITS("") == ([], 0)

    def test_whitespace_only(self):
        assert PARSE_HEX_BITS("   ") == ([], 0)

    def test_invalid_hex_raises(self):
        with pytest.raises(ValueError, match="不合法的十六进制数据"):
            PARSE_HEX_BITS("ZZZZ")

    # --- last_bits 参数测试 ---

    def test_with_last_bits(self):
        """last_bits=4 截断最后一个字节: 0x11 → 0x01"""
        assert PARSE_HEX_BITS("00 11", last_bits=4) == ([0x00, 0x01], 4)

    def test_with_last_bits_single_byte(self):
        """last_bits=7 截断: 0xFF → 0x7F"""
        assert PARSE_HEX_BITS("FF", last_bits=7) == ([0x7F], 7)

    def test_with_last_bits_no_space(self):
        assert PARSE_HEX_BITS("0011", last_bits=4) == ([0x00, 0x01], 4)

    # --- Verilog 标记：无截断 ---

    def test_verilog_no_truncate(self):
        """值在 bits 范围内，无需截断"""
        assert PARSE_HEX_BITS("7'h03") == ([0x03], 7)

    def test_verilog_no_truncate_even(self):
        """偶数位 hex，无需填充"""
        assert PARSE_HEX_BITS("8'hFF") == ([0xFF], 8)

    def test_verilog_no_truncate_4bits(self):
        """4 位 hex 值，无需截断"""
        assert PARSE_HEX_BITS("4'hA") == ([0x0A], 4)

    def test_verilog_no_truncate_4bits_max(self):
        """4 位最大值 F，无需截断"""
        assert PARSE_HEX_BITS("4'hF") == ([0x0F], 4)

    # --- Verilog 标记：截断高位 ---

    def test_verilog_truncate_4bits(self):
        """4'hCA → 截断高位 C，只保留 4 位 → 0x0A"""
        assert PARSE_HEX_BITS("4'hCA") == ([0x0A], 4)

    def test_verilog_truncate_7bits(self):
        """7'hFF → FF 是 8 位，截断为 7 位 → 0x7F"""
        assert PARSE_HEX_BITS("7'hFF") == ([0x7F], 7)

    def test_verilog_truncate_4bits_bigger(self):
        """4'hFF → 截断为 4 位 → 0x0F"""
        assert PARSE_HEX_BITS("4'hFF") == ([0x0F], 4)

    def test_verilog_truncate_1bit(self):
        """1'h1 → 1 位最大值 1"""
        assert PARSE_HEX_BITS("1'h1") == ([0x01], 1)

    def test_verilog_truncate_1bit_zero(self):
        """1'h0 → 1 位最小值 0"""
        assert PARSE_HEX_BITS("1'h0") == ([0x00], 1)

    # --- Verilog 标记：奇数位填充 ---

    def test_verilog_odd_pad(self):
        """4'hB → 奇数位填充为 0B"""
        assert PARSE_HEX_BITS("4'hB") == ([0x0B], 4)

    def test_verilog_odd_pad_7bits(self):
        """7'hA → 奇数位填充为 0A，7 位无需截断"""
        assert PARSE_HEX_BITS("7'hA") == ([0x0A], 7)

    def test_verilog_odd_pad_truncate(self):
        """4'hCB → 奇数位填充后截断 → 0x0B"""
        assert PARSE_HEX_BITS("4'hCB") == ([0x0B], 4)

    # --- 混合格式 ---

    def test_mixed_hex_and_verilog(self):
        """4'hBB → 截断为 4 位 → 0x0B"""
        assert PARSE_HEX_BITS("AA 4'hBB") == ([0xAA, 0x0B], 4)

    def test_mixed_verilog_last(self):
        """Verilog 标记在最后"""
        assert PARSE_HEX_BITS("AA BB 7'h03") == ([0xAA, 0xBB, 0x03], 7)

    def test_mixed_no_space_verilog_end(self):
        """AABB7'h26 → 正常解析"""
        assert PARSE_HEX_BITS("AABB7'h26") == ([0xAA, 0xBB, 0x26], 7)

    # --- 冲突检测 ---

    def test_verilog_and_last_bits_conflict(self):
        with pytest.raises(ValueError, match="冲突"):
            PARSE_HEX_BITS("AA 4'hBB", last_bits=4)

    def test_multiple_verilog_marks_error(self):
        """多个 Verilog 标记报错"""
        with pytest.raises(ValueError, match="只允许一个"):
            PARSE_HEX_BITS("7'h03 AA 4'hC")

    # --- 小写 hex ---

    def test_verilog_lower_hex(self):
        assert PARSE_HEX_BITS("7'h0a") == ([0x0A], 7)

    def test_verilog_lower_hex_truncate(self):
        """4'hca → 截断为 4 位 → 0x0A"""
        assert PARSE_HEX_BITS("4'hca") == ([0x0A], 4)


class TestFORMAT_HEX:
    """FORMAT_HEX: 格式化为可视化 hex"""

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


class TestRoundtrip:
    """PARSE_HEX <-> FORMAT_HEX 往返测试"""

    def test_roundtrip_no_bits(self):
        data = [0xAA, 0xBB, 0xCC]
        formatted = FORMAT_HEX(data)
        parsed = PARSE_HEX(formatted)
        assert parsed == data

    def test_roundtrip_with_bits(self):
        data = [0xAA, 0xBB, 0x03]
        formatted = FORMAT_HEX(data, 7)
        parsed, bits = PARSE_HEX_BITS(formatted)
        assert parsed == data
        assert bits == 7

    def test_roundtrip_single_byte(self):
        """4'hFF 会被截断为 4 位 → 0x0F"""
        formatted = FORMAT_HEX(0xFF, 4)
        parsed, bits = PARSE_HEX_BITS(formatted)
        assert parsed == [0x0F]
        assert bits == 4
