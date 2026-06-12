import re

# 位标记正则：匹配 N'hXX 格式 (如 7'h26, 4'hC)
BIT_PATTERN = re.compile(r"(\d+)\s*\'h\s*([0-9a-fA-F]+)")

def PARSE_HEX(text: str) -> tuple[str, int]:
    """
    解析文本 -> (纯十六进制字符串, 最后字节有效位数)
    支持: "AA BB 7'h03" -> ("AABB03", 7)
    """
    last_bits = 0
    cleaned = text.strip()

    # 查找所有位标记
    matches = list(BIT_PATTERN.finditer(cleaned))
    if matches:
        last_match = matches[-1]
        last_bits = int(last_match.group(1))
        hex_val = last_match.group(2)
        
        # 替换位标记为纯 hex
        cleaned = cleaned[:last_match.start()] + hex_val + cleaned[last_match.end():]

    # 去空格得到纯 hex
    clean_hex = cleaned.replace(" ", "")
    
    # 简单的合法性检查
    if clean_hex:
        try:
            bytes.fromhex(clean_hex)
        except ValueError:
            raise ValueError(f"不合法的十六进制数据: {clean_hex}")

    return clean_hex, last_bits

def FORMAT_HEX(data: int | bytes | list[int] | str, last_bits: int = 0) -> str:
    """
    格式化数据为带位标记的可视化格式
    支持输入类型: int, bytes, list[int], str (纯 hex)
    示例:
        FORMAT_HEX(0xAABB03, 7)        -> "AA BB 7'h03"
        FORMAT_HEX("AABB03", 7)        -> "AA BB 7'h03"
        FORMAT_HEX(b'\xaa\xbb\x03', 7) -> "AA BB 7'h03"
        FORMAT_HEX([0xAA, 0xBB, 0x03], 7) -> "AA BB 7'h03"
    """
    # 1. 统一转换为纯十六进制字符串
    if isinstance(data, int):
        hex_str = hex(data)[2:].upper()
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
        parsed_h, parsed_b = PARSE_HEX(formatted)
        print(f"解析: {formatted} -> Hex: {parsed_h}, Bits: {parsed_b}")
        print("-" * 20)
