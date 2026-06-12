from typing import Any

from .assertions import ASSERT_EQUAL, ASSERT_IS_NOT_NONE, ASSERT_LEN
from .checksum import GET_BCC
from .hex_util import FORMAT_HEX
from nfctester.hardware.serial_transport import SerialTransport
from nfctester.drivers.pn532_hsu import PN532_HSU

# Global state
_transport: SerialTransport | None = None
_driver: PN532_HSU | None = None
_is_connected = False

def connect(port="COM20"):
    """
    连接并初始化 PN532 读卡器。

    Args:
        port: 串口号，默认为 "COM20"。
    """
    global _transport, _driver, _is_connected
    _transport = SerialTransport(port=port)
    _driver = PN532_HSU(_transport)
    _driver.connect()
    _is_connected = True
    print(f"Connected to PN532 on {_transport.ser.port}")

def active(ll: bool = False, ignore_error: bool = False) -> dict | None:
    """
    寻卡操作，检测并激活目标卡片。

    Args:
        ll: 如果为 True，则执行底层抗冲突流程以兼容非标卡；
            如果为 False，则使用 PN532 原生 find()。
        ignore_error: 如果为 True，当 BCC 或 SAK 校验失败时，记录警告而不停止执行。

    Returns:
        dict: 包含卡片信息的字典，失败时返回 None。
              Key 说明:
              - 'uid' (bytes): 卡片的 UID。
              - 'atq' (bytes): 卡片的 ATQ (Answer To Request)。
              - 'sak' (int):   卡片的 SAK (Select Acknowledge)。
              - 'raw' (bytes): PN532 返回的原始响应数据。
    """
    ASSERT_IS_NOT_NONE(_driver, msg="NFC driver not connected. Call connect() first.")
        
    if not ll:
        return _driver.find()
    else:
        # 手动底层寻卡流程
        # 1. REQA
        res_reqa = reqa()
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
                if not ignore_error: ASSERT_IS_NOT_NONE(sak_res, msg=f"CL{cl} SAK 选择失败")
                else: print(f"Warning: CL{cl} SAK 选择失败")
            
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
            'raw': bytes(full_uid) # 兼容原有的 raw 字段
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
    ASSERT_IS_NOT_NONE(_driver, msg="NFC driver not connected.")
    _driver.set_crc(tx_crc, rx_crc)
    res = _driver.transceive(bytes(data))
    # print(f"transceive: {FORMAT_HEX(data)}")
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
    ASSERT_IS_NOT_NONE(_driver, msg="NFC driver not connected.")
    _driver.set_crc(tx_crc, rx_crc)
    res = _driver.transceive(bytes(data), last_tx_bits=last_tx_bits)
    # print(f"transceive: {FORMAT_HEX(data, last_tx_bits)}")
    return (list(res) if res is not None else []), _driver.last_rx_bits

def reqa() -> tuple[list[int], int] | None:
    """ISO14443-A REQA (7 bits)"""
    # REQA: 0x26，短帧，仅发送 7 bits，响应无 CRC
    return transceive_bits([0x26], last_tx_bits=7, tx_crc=False, rx_crc=False)

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
    ASSERT_IS_NOT_NONE(_driver, msg="NFC driver not connected.")
    _driver.set_rf_field(True)

def field_off():
    """关闭 PN532 的 RF 场。"""
    ASSERT_IS_NOT_NONE(_driver, msg="NFC driver not connected.")
    _driver.set_rf_field(False)

def close():
    """
    断开与 PN532 读卡器的连接。
    """
    global _is_connected
    if _is_connected and _driver:
        _driver.disconnect()
        _is_connected = False
        print("Disconnected")
