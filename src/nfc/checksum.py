from .assertions import ASSERT_LEN
from .hex_util import FORMAT_HEX

def GET_BCC(data: list[int]) -> int:
    """
    计算 BCC: data[0]^data[1]^data[2]^data[3]。

    Args:
        data: 4 字节的 UID 数据。

    Returns:
        int: 异或校验值。

    Raises:
        AssertionError: 输入数据长度不为 4 时抛出。
    """
    ASSERT_LEN(data, 4, msg=f"计算BCC时输入数据长度应为4: {FORMAT_HEX(data)}")
    return data[0] ^ data[1] ^ data[2] ^ data[3]
