from .hex_util import FORMAT_HEX

def BITS_UPDATE(val: int, mask: int, data: int) -> int:
    """
    更新寄存器中的特定位域 (Read-Modify-Write)。

    Args:
        val: 当前寄存器的原始值。
        mask: 预移位的位掩码 (例如: 0x20)。
        data: 已移位对齐的新数值 (例如: 0x20, 即 1 << 5)。

    Returns:
        int: 更新后的寄存器值。
    """
    assert (data & ~mask) == 0, f"Data {FORMAT_HEX(data)} contains bits outside mask {FORMAT_HEX(mask)}"
    return (val & ~mask) | (data & mask)

def BITS_SET(val: int, mask: int) -> int:
    """
    将寄存器中的指定位强制置 1 (OR 操作)。

    Args:
        val: 当前寄存器的原始值。
        mask: 想要置 1 的位掩码。

    Returns:
        int: 置位后的寄存器值。
    """
    return val | mask

def BITS_RESET(val: int, mask: int) -> int:
    """
    将寄存器中的指定位强制清 0 (AND-NOT 操作)。

    Args:
        val: 当前寄存器的原始值。
        mask: 想要清 0 的位掩码。

    Returns:
        int: 清位后的寄存器值。
    """
    return val & ~mask
