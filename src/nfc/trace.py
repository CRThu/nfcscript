"""
NFC Script Trace 模块

提供日志追踪控制，包装 nfctester.trace 的功能。
"""

from typing import Callable
from nfctester.trace import TraceEvent, trace as _trace


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
        level: 0=关闭(hex), 1=简单(hex + 摘要标签)
    """
    _trace.set_parse(level)


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


def add_sink(fn: Callable[[TraceEvent], None]):
    """
    注册结构化 trace 事件回调。

    Args:
        fn: 回调函数，接收 TraceEvent 对象
    """
    _trace.add_sink(fn)


def remove_sink(fn: Callable[[TraceEvent], None]):
    """
    移除结构化 trace 事件回调。

    Args:
        fn: 之前注册的回调函数
    """
    _trace.remove_sink(fn)
