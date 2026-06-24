"""
NFC Script Trace 模块

提供日志追踪控制，包装 nfctester.trace 的功能。
"""

from nfctester.trace import trace as _trace


def set_layer(layer: str, enable: bool = True):
    """
    开启或关闭追踪层。

    Args:
        layer: 层级名称 ("DRIVER" 或 "PROTOCOL")
        enable: True 开启，False 关闭
    """
    _trace.set_layer(layer, enable)


def set_level(level: str):
    """
    设置日志级别。

    Args:
        level: 级别名称 ("INFO", "DEBUG", "ERROR" 等)
    """
    _trace.set_level(level)


def set_parse(level: int = 1):
    """
    设置解析级别。

    Args:
        level: 0=关闭, 1=简单(一行摘要), 2=复杂(树状结构)
    """
    _trace.set_parse(level)


def set_card_type(card_type: str):
    """
    设置当前卡片类型，注入到所有协议解析器的 state 中。

    Args:
        card_type: 卡片类型标识，如 "mifare_classic_1k", "ntag213"
    """
    _trace.set_card_type(card_type)


def info(msg: str):
    """输出 INFO 级别日志"""
    _trace.info(msg)


def error(msg: str):
    """输出 ERROR 级别日志"""
    _trace.error(msg)


def warning(msg: str):
    """输出 WARNING 级别日志"""
    _trace.warning(msg)


def success(msg: str):
    """输出 SUCCESS 级别日志"""
    _trace.success(msg)


def debug(msg: str):
    """输出 DEBUG 级别日志"""
    _trace.debug(msg)
