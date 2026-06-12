from .assertions import ASSERT_LEN
from .hex_util import FORMAT_HEX

def GET_BCC(data: list[int]) -> int:
    """
    计算 BCC: data[0]^data[1]^data[2]^data[3]
    :param data: 4字节的UID数据
    """
    ASSERT_LEN(data, 4, msg=f"计算BCC时输入数据长度应为4: {FORMAT_HEX(data)}")
    return data[0] ^ data[1] ^ data[2] ^ data[3]
