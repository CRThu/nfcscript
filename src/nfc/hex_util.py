import re

# 位标记正则：匹配 N'hXX 格式 (如 7'h26, 4'hC)
BIT_PATTERN = re.compile(r"(\d+)\s*\'h\s*([0-9a-fA-F]+)")


def PARSE_HEX(text: str) -> list[int]:
    """
    解析纯 hex 字符串为 list[int]。

    Args:
        text: 十六进制文本，支持空格分隔 (如 "AA BB CC" 或 "AABBCC")。

    Returns:
        list[int]: 解析后的字节列表。

    Raises:
        ValueError: 不合法的十六进制数据时抛出。

    Examples:
        >>> PARSE_HEX("AA BB CC")
        [0xAA, 0xBB, 0xCC]
        >>> PARSE_HEX("0011")
        [0x00, 0x11]
    """
    # 去空格得到纯 hex
    clean_hex = text.replace(" ", "").upper()

    # 简单的合法性检查
    if clean_hex:
        try:
            return list(bytes.fromhex(clean_hex))
        except ValueError:
            raise ValueError(f"不合法的十六进制数据: {clean_hex}")
    return []


def PARSE_HEX_BITS(text: str, last_bits: int | None = None) -> tuple[list[int], int]:
    """
    解析 hex 字符串为 tuple[list[int], int]，支持 Verilog 位标记。

    支持格式:
    - 纯 hex: "AA BB CC" → ([0xAA, 0xBB, 0xCC], 0)
    - Verilog 标记: "AA 4'hBB" → ([0xAA, 0x0B], 4)
    - 混合: "AA BB 7'h03" → ([0xAA, 0xBB, 0x03], 7)
    - 手动指定: "AA BB", last_bits=4 → ([0xAA, 0xBB], 4)

    Args:
        text: 十六进制文本，支持空格分隔和 N'hXX 位标记。
        last_bits: 可选的最后字节有效位数，与 Verilog 标记冲突时报错。

    Returns:
        tuple[list[int], int]: (字节列表, 最后字节有效位数)。

    Raises:
        ValueError: 不合法的十六进制数据、位标记冲突或多标记时报错。

    Examples:
        >>> PARSE_HEX_BITS("AA BB CC")
        ([0xAA, 0xBB, 0xCC], 0)
        >>> PARSE_HEX_BITS("AA 4'hBB")
        ([0xAA, 0x0B], 4)
        >>> PARSE_HEX_BITS("0011", last_bits=4)
        ([0x00, 0x01], 4)
        >>> PARSE_HEX_BITS("AA 4'hBB", last_bits=4)
        ValueError: 冲突
    """
    # 冲突检测：只允许一个 Verilog 标记
    matches = list(BIT_PATTERN.finditer(text))
    if len(matches) > 1:
        raise ValueError("只允许一个 Verilog 位标记")
    if matches and last_bits is not None:
        raise ValueError("last_bits 参数与 Verilog 位标记冲突")

    bits = last_bits if last_bits is not None else 0

    # 处理 Verilog 位标记
    if matches:
        m = matches[0]
        n_bits = int(m.group(1))
        bits = n_bits
        # 按 bits 截断: 4'hCA → 0x0A
        val = int(m.group(2), 16) & ((1 << n_bits) - 1)
        hex_val = format(val, 'X')
        if len(hex_val) % 2 != 0:
            hex_val = '0' + hex_val
        text = text[:m.start()] + hex_val + text[m.end():]

    # 去空格得到纯 hex
    clean_hex = text.replace(" ", "").upper()

    # 解析 hex 数据
    if clean_hex:
        try:
            data = list(bytes.fromhex(clean_hex))
        except ValueError:
            raise ValueError(f"不合法的十六进制数据: {clean_hex}")
    else:
        data = []

    # last_bits 截断最后一个字节
    if bits and data:
        data[-1] = data[-1] & ((1 << bits) - 1)

    return data, bits


def FORMAT_HEX(data: int | bytes | list[int] | str, last_bits: int = 0) -> str:
    """
    格式化数据为带位标记的可视化格式。

    支持输入类型: int, bytes, list[int], str (纯 hex)。

    Args:
        data: 待格式化的数据。
        last_bits: 最后一个字节的有效位数 (1-7)，0 表示整字节。

    Returns:
        str: 格式化后的字符串。

    Raises:
        TypeError: 不支持的输入类型时抛出。

    Examples:
        >>> FORMAT_HEX(0xAABB03, 7)
        "AA BB 7'h03"
        >>> FORMAT_HEX([0xAA, 0xBB, 0x03])
        'AA BB 03'
        >>> FORMAT_HEX("AABB", 4)
        "AA 4'hBB"
    """
    # 1. 统一转换为纯十六进制字符串
    if isinstance(data, int):
        hex_str = data.to_bytes(max(1, (data.bit_length() + 7) // 8)).hex().upper()
    elif isinstance(data, bytes):
        hex_str = data.hex().upper()
    elif isinstance(data, list):
        hex_str = bytes(data).hex().upper()
    elif isinstance(data, str):
        hex_str = data.replace(" ", "").upper()
    else:
        raise TypeError(f"不支持的输入类型: {type(data)}")

    if not hex_str:
        return ""

    # 2. 如果是整字节 (无 last_bits)
    if last_bits == 0:
        return ' '.join(hex_str[i:i+2] for i in range(0, len(hex_str), 2))

    # 3. 有 last_bits，处理最后一个字节
    if len(hex_str) <= 2:
        return f"{last_bits}'h{hex_str}"

    prefix = hex_str[:-2]
    last_byte = hex_str[-2:]
    formatted_prefix = ' '.join(prefix[i:i+2] for i in range(0, len(prefix), 2))
    return f"{formatted_prefix} {last_bits}'h{last_byte}"


if __name__ == "__main__":
    # --- 测试例程 ---
    print("=== Hex 工具测试 ===")

    # 测试用例: (data, last_bits, 类型名)
    test_cases = [
        ("AABB03", 7, "str"),
        (0xAABB03, 7, "int"),
        (b'\xAA\xBB\x03', 7, "bytes"),
        ([0xAA, 0xBB, 0x03], 7, "list"),
        ("FF", 4, "str"),
        (0xFF, 4, "int"),
        ("AABBCC", 0, "str"),
        (0xAABBCC, 0, "int"),
        (b'\xAA\xBB\xCC', 0, "bytes"),
    ]

    for data, b, typename in test_cases:
        formatted = FORMAT_HEX(data, b)
        print(f"输入: ({data}, {b}, {typename}) -> 格式化: {formatted}")

        # 反向解析验证
        if b:
            parsed, bits = PARSE_HEX_BITS(formatted)
            print(f"解析: {formatted} -> Hex: {parsed}, Bits: {bits}")
        else:
            parsed = PARSE_HEX(formatted)
            print(f"解析: {formatted} -> Hex: {parsed}")
        print("-" * 20)
