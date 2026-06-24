import os
from contextlib import contextmanager
from nfctester.registry import CardReaderRegistry
from .assertions import ASSERT_EQUAL, ASSERT_IS_NOT_NONE, ASSERT_LEN
from .checksum import GET_BCC
from .hex_util import FORMAT_HEX


class _NFCState:
    """单例状态管理，封装读卡器生命周期"""

    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._reader = None
            cls._instance._connected = False
        return cls._instance

    @property
    def reader(self):
        return self._reader

    def connect(self, port: str = "COM20", reader_type: str = "pn532"):
        self._reader = CardReaderRegistry.create(reader_type, transport="serial", port=port)
        self._reader.connect()
        self._connected = True
        print(f"Connected to {reader_type.upper()} on port {port}")

    def disconnect(self):
        if self._connected and self._reader:
            self._reader.disconnect()
            self._connected = False
            self._reader = None
            print("Disconnected")

    def ensure_connected(self):
        ASSERT_IS_NOT_NONE(self._reader, msg="NFC driver not connected. Call connect() first.")


_state = _NFCState()


def connect(port: str = None, reader_type: str = None):
    """
    连接并初始化读卡器。

    Args:
        port: 串口号，若未指定则从环境变量 NFC_PORT 读取。
        reader_type: 读卡器类型，若未指定则从环境变量 NFC_READER 读取。

    Raises:
        ValueError: 未提供 port 或 reader_type 且环境变量未设置。
    """
    if port is None:
        port = os.environ.get("NFC_PORT")
    if reader_type is None:
        reader_type = os.environ.get("NFC_READER")
    if port is None:
        raise ValueError("未指定串口，请通过 -p 参数、connect(port=...) 或 NFC_PORT 环境变量配置")
    if reader_type is None:
        raise ValueError("未指定读卡器类型，请通过 -r 参数、connect(reader_type=...) 或 NFC_READER 环境变量配置")
    _state.connect(port, reader_type)


def get_reader():
    """
    获取当前连接的读卡器实例，供 Card 类使用。

    Returns:
        reader: 当前连接的读卡器实例。
    """
    _state.ensure_connected()
    return _state.reader


def active(ll: bool = False, ignore_error: bool = False, reqa_cmd: int = 0x26) -> dict | None:
    """
    寻卡操作，检测并激活目标卡片。

    Args:
        ll: 如果为 True，则执行底层抗冲突流程以兼容非标卡；
            如果为 False，则使用 PN532 原生 find()。
        ignore_error: 如果为 True，当 BCC 或 SAK 校验失败时，记录警告而不停止执行。
        reqa_cmd: 底层寻卡时使用的 REQA 命令字节，默认 0x26。
                  仅在 ll=True 时生效。

    Returns:
        dict: 包含卡片信息的字典，失败时返回 None。
              Key 说明:
              - 'uid' (bytes): 卡片的 UID。
              - 'atq' (bytes): 卡片的 ATQ (Answer To Request)。
              - 'sak' (int):   卡片的 SAK (Select Acknowledge)。
              - 'raw' (bytes): PN532 返回的原始响应数据。
    """
    _state.ensure_connected()
    reader = _state.reader

    if not ll:
        return reader.find()

    # 手动底层寻卡流程
    # 1. REQA
    res_reqa = reqa(cmd=reqa_cmd)
    if not res_reqa:
        return None
    atq = bytes(res_reqa[0])

    # 2. 抗冲突与选择
    full_uid = []
    sak = 0
    for cl in [1, 2, 3]:
        res = anticoll(cl_level=cl, nvb=0x20)
        if not res or not res[0]:
            return None

        data = res[0]
        # 只有当有数据时才进行长度校验
        if len(data) > 0:
            ASSERT_LEN(data, 5, msg=f"CL{cl} 抗冲突返回数据长度不符: {FORMAT_HEX(data)}")

            # 计算期望的 BCC
            expected_bcc = GET_BCC(data[0:4])

            if not ignore_error:
                ASSERT_EQUAL(expected_bcc, data[4], msg=f"CL{cl} BCC 校验失败: data={FORMAT_HEX(data)}")
            elif data[4] != expected_bcc:
                print(f"Warning: CL{cl} BCC 校验失败")

        has_next = (data[0] == 0x88)
        uid_to_select = data[0:5]
        sak_res = select(cl_level=cl, uid=uid_to_select)

        # SAK 校验
        if not sak_res:
            if not ignore_error:
                ASSERT_IS_NOT_NONE(sak_res, msg=f"CL{cl} SAK 选择失败")
            else:
                print(f"Warning: CL{cl} SAK 选择失败")

        if has_next:
            full_uid.extend(data[1:4])
        else:
            full_uid.extend(data[0:4])
            # 记录最后一次 SELECT 的 SAK
            sak = sak_res[0] if sak_res else 0
            break

    # 返回兼容的字典格式
    return {
        'uid': bytes(full_uid),
        'atq': atq,
        'sak': sak,
        'raw': bytes(full_uid),  # 兼容原有的 raw 字段
    }


def transceive(data: list[int], tx_crc: bool = True, rx_crc: bool = True) -> list[int]:
    """
    使用底层帧交互方式发送数据。

    Args:
        data: 要发送的字节列表。
        tx_crc: 发送时是否自动添加 CRC。
        rx_crc: 接收时是否自动校验 CRC。

    Returns:
        list[int]: 接收到的数据字节列表。
    """
    _state.ensure_connected()
    reader = _state.reader
    reader.set_crc(tx_crc, rx_crc)
    res = reader.transceive(bytes(data))
    return list(res) if res is not None else []


def transceive_bits(data: list[int], last_tx_bits: int = 0, tx_crc: bool = True, rx_crc: bool = True) -> tuple[list[int], int]:
    """
    使用底层帧交互方式发送数据，并支持对最后一个字节进行位控制。

    Args:
        data: 要发送的字节列表。
        last_tx_bits: 最后一个字节实际发送的有效位数 (1-7)，
                      0 表示发送完整字节。
        tx_crc: 发送时是否自动添加 CRC。
        rx_crc: 接收时是否自动校验 CRC。

    Returns:
        tuple[list[int], int]: (接收到的数据字节列表, 最后一个字节的有效位数)。
                               最后一个字节的有效位数 0 表示完整字节。
    """
    _state.ensure_connected()
    reader = _state.reader
    reader.set_crc(tx_crc, rx_crc)
    res = reader.transceive(bytes(data), last_tx_bits=last_tx_bits)
    return (list(res) if res is not None else []), reader.last_rx_bits


def reqa(cmd: int = 0x26) -> tuple[list[int], int] | None:
    """ISO14443-A REQA (7 bits)"""
    # REQA: 0x26，短帧，仅发送 7 bits，响应无 CRC
    return transceive_bits([cmd], last_tx_bits=7, tx_crc=False, rx_crc=False)


def wupa() -> tuple[list[int], int] | None:
    """ISO14443-A WUPA (7 bits)"""
    # WUPA: 0x52，短帧，仅发送 7 bits，响应无 CRC
    return transceive_bits([0x52], last_tx_bits=7, tx_crc=False, rx_crc=False)


def halt() -> list[int] | None:
    """ISO14443-A HALT (Standard Frame)"""
    # HALT: 0x50 0x00 + CRC
    return transceive([0x50, 0x00], tx_crc=True, rx_crc=True)


def anticoll(cl_level: int, nvb: int = 0x20, uid_prefix: list[int] = []) -> tuple[list[int], int] | None:
    """
    ISO14443-A ANTICOLL (Anti-collision)
    :param cl_level: 1 (0x93) or 2 (0x95)
    :param nvb: Number of Valid Bits，定义了包含 SEL 和 NVB 在内的有效位数
    :param uid_prefix: 已知的部分 UID (0-4 字节)
    :return: (响应数据, last_rx_bits)
    """
    cmd = [0x93 if cl_level == 1 else 0x95, nvb] + uid_prefix
    # 抗冲突响应无 CRC
    return transceive_bits(cmd, last_tx_bits=0, tx_crc=False, rx_crc=False)


def select(cl_level: int, uid: list[int]) -> list[int] | None:
    """
    ISO14443-A SELECT (Standard Frame)
    :param cl_level: 1 (0x93) or 2 (0x95)
    :param uid: 完整 5 字节 UID (包含 BCC)
    """
    cmd = [0x93 if cl_level == 1 else 0x95, 0x70] + uid
    # 选择帧需带 CRC
    return transceive(cmd, tx_crc=True, rx_crc=True)


def field_on():
    """开启 PN532 的 RF 场。"""
    _state.ensure_connected()
    _state.reader.set_rf_field(True)


def field_off():
    """关闭 PN532 的 RF 场。"""
    _state.ensure_connected()
    _state.reader.set_rf_field(False)


def close():
    """
    断开与 PN532 读卡器的连接。
    """
    _state.disconnect()


@contextmanager
def session(port: str = None, reader_type: str = None):
    """
    上下文管理器，自动管理连接生命周期。

    用法:
        with session("COM20") as reader:
            card_info = reader.find()
    """
    if port is None:
        port = os.environ.get("NFC_PORT")
    if reader_type is None:
        reader_type = os.environ.get("NFC_READER")
    if port is None:
        raise ValueError("未指定串口，请通过 session(port=...) 或 NFC_PORT 环境变量配置")
    if reader_type is None:
        raise ValueError("未指定读卡器类型，请通过 session(reader_type=...) 或 NFC_READER 环境变量配置")
    _state.connect(port, reader_type)
    try:
        yield _state.reader
    finally:
        _state.disconnect()
