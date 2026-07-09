import os
from contextlib import contextmanager
from nfctester.drivers.card_reader import CardInfo, TransceiveBits
from nfctester.registry import CardReaderRegistry
from nfctester.trace import trace as _trace
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
        self._reader.open()
        self._connected = True
        print(f"Connected to {reader_type.upper()} on port {port}")

    def disconnect(self):
        if self._connected and self._reader:
            self._reader.close()
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


def active(low_layer: bool = False, ignore_error: bool = False, reqa_cmd: int = 0x26) -> CardInfo | None:
    """
    寻卡操作，检测并激活目标卡片。

    Args:
        low_layer: 如果为 True，由 nfcscript 执行底层抗冲突流程以兼容非标卡；
            如果为 False，则使用读卡器驱动层原生 active()。
        ignore_error: 如果为 True，当 BCC 或 SAK 校验失败时，记录警告而不停止执行。
        reqa_cmd: 底层寻卡时使用的 REQA 命令字节，默认 0x26。仅 low_layer=True 时生效。

    Returns:
        CardInfo: 包含卡片信息的数据类，失败时返回 None。
              属性说明:
              - 'uid' (list[int]): 卡片的 UID。
              - 'atq' (list[int]): 卡片的 ATQ (Answer To Request)。
              - 'sak' (int):   卡片的 SAK (Select Acknowledge)。
    """
    _state.ensure_connected()
    reader = _state.reader

    if not low_layer:
        return reader.active()

    # 手动底层寻卡流程
    # 1. REQA
    res_reqa = reqa(cmd=reqa_cmd)
    if not res_reqa.data:
        return None
    atq = res_reqa.data

    # 2. 抗冲突与选择
    full_uid = []
    for cl in [1, 2, 3]:
        res = anticoll(cl_level=cl, nvb=0x20)
        if not res.data:
            return None

        data = res.data
        # 只有当有数据时才进行长度校验
        if len(data) > 0:
            ASSERT_LEN(data, 5, msg=f"CL{cl} 抗冲突返回数据长度不符: {FORMAT_HEX(data)}")

            # 计算期望的 BCC
            expected_bcc = GET_BCC(data[0:4])

            if not ignore_error:
                ASSERT_EQUAL(expected_bcc, data[4], msg=f"CL{cl} BCC 校验失败: data={FORMAT_HEX(data)}")
            elif data[4] != expected_bcc:
                print(f"Warning: CL{cl} BCC 校验失败")

        print(f"cl{cl}.uid: {FORMAT_HEX(data)}")
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
            # SAK 为最后一次 SELECT 响应的第 1 个字节 (int)
            sak = sak_res[0] if sak_res else 0
            break

    info = CardInfo(uid=full_uid, atq=atq, sak=sak)
    atqa = int.from_bytes(atq, "little")
    _trace.set_parser(atqa, sak)
    return info


def transceive(data: list[int], tx_crc: bool = True, rx_crc: bool = True) -> list[int]:
    """
    使用底层帧交互方式发送数据。

    Args:
        data: 要发送的字节列表。
        tx_crc: 发送时是否自动添加 CRC。False 则原样发送。
        rx_crc: 接收时是否自动校验 CRC。False 则原样接收不校验。

    Returns:
        list[int]: 接收到的数据字节列表。
    """
    _state.ensure_connected()
    reader = _state.reader
    res = reader.transceive(data, tx_crc=tx_crc, rx_crc=rx_crc)
    return res.data if res and res.data else []


def transceive_bits(data: list[int], last_tx_bits: int = 0, tx_crc: bool = True, rx_crc: bool = True) -> TransceiveBits:
    """
    使用底层帧交互方式发送数据，并支持对最后一个字节进行位控制。

    Args:
        data: 要发送的字节列表。
        last_tx_bits: 最后一个字节实际发送的有效位数 (1-7)，0 表示发送完整字节。
        tx_crc: 发送时是否自动添加 CRC。False 则原样发送。
        rx_crc: 接收时是否自动校验 CRC。False 则原样接收不校验。

    Returns:
        TransceiveBits: 包含 data 和 bits 属性，失败返回空的 TransceiveBits(data=[], bits=0)。
    """
    _state.ensure_connected()
    reader = _state.reader
    res = reader.transceive(data, last_tx_bits=last_tx_bits, tx_crc=tx_crc, rx_crc=rx_crc)
    return res if res else TransceiveBits(data=[], bits=0)


def reqa(cmd: int = 0x26) -> TransceiveBits:
    """
    ISO14443-A REQA (7 bits)。

    Args:
        cmd: REQA 命令字节，默认 0x26。

    Returns:
        TransceiveBits: 包含 data 和 bits 属性，失败返回空的 TransceiveBits(data=[], bits=0)。
    """
    return transceive_bits([cmd], last_tx_bits=7, tx_crc=False, rx_crc=False)


def wupa() -> TransceiveBits:
    """
    ISO14443-A WUPA (7 bits)。

    Returns:
        TransceiveBits: 包含 data 和 bits 属性，失败返回空的 TransceiveBits(data=[], bits=0)。
    """
    return transceive_bits([0x52], last_tx_bits=7, tx_crc=False, rx_crc=False)


def halt() -> list[int]:
    """
    ISO14443-A HALT (Standard Frame)。

    Returns:
        list[int]: 返回响应数据。
    """
    return transceive([0x50, 0x00], tx_crc=True, rx_crc=True)


def _get_sel_cmd(cl_level: int) -> int:
    """
    根据 CL 级别获取 ISO14443-A SEL 命令字节。

    Args:
        cl_level: CL 级别，1/2/3。

    Returns:
        int: 对应的 SEL 命令字节 (0x93/0x95/0x97)。

    Raises:
        ValueError: CL 级别不在 1/2/3 范围内。
    """
    sel_map = {1: 0x93, 2: 0x95, 3: 0x97}
    if cl_level not in sel_map:
        raise ValueError(f"Invalid CL level: {cl_level}, must be 1, 2, or 3")
    return sel_map[cl_level]


def anticoll(cl_level: int, nvb: int = 0x20, uid_prefix: list[int] = []) -> TransceiveBits:
    """
    ISO14443-A ANTICOLL (Anti-collision)。

    Args:
        cl_level: CL 级别，1 (0x93), 2 (0x95), 或 3 (0x97)。
        nvb: Number of Valid Bits，定义了包含 SEL 和 NVB 在内的有效位数。
        uid_prefix: 已知的部分 UID (0-4 字节)。

    Returns:
        TransceiveBits: 包含 data 和 bits 属性，失败返回空的 TransceiveBits(data=[], bits=0)。
    """
    cmd = [_get_sel_cmd(cl_level), nvb] + uid_prefix
    return transceive_bits(cmd, last_tx_bits=0, tx_crc=False, rx_crc=False)


def select(cl_level: int, uid: list[int]) -> list[int]:
    """
    ISO14443-A SELECT (Standard Frame)。

    Args:
        cl_level: CL 级别，1 (0x93), 2 (0x95), 或 3 (0x97)。
        uid: 完整 5 字节 UID (包含 BCC)。

    Returns:
        list[int]: 返回响应数据。
    """
    cmd = [_get_sel_cmd(cl_level), 0x70] + uid
    return transceive(cmd, tx_crc=True, rx_crc=True)


def field_on():
    """
    开启 PN532 的 RF 场。

    Raises:
        AssertionError: 未连接读卡器时抛出。
    """
    _state.ensure_connected()
    _state.reader.rf_field = True


def field_off():
    """
    关闭 PN532 的 RF 场。

    Raises:
        AssertionError: 未连接读卡器时抛出。
    """
    _state.ensure_connected()
    _state.reader.rf_field = False


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
            card_info = reader.active()
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
