"""
NFC Script Trace 模块

统一日志 API，包装 nfctester.trace 的 6 层日志系统。
层: driver, debug, protocol, warning, error, app

支持两种控制方式：
1. 属性控制: trace.driver = True, trace.level = "warning"
2. 方法控制: trace.set_layer("driver", True), trace.set_level("warning")
"""

from typing import Callable
from nfctester.trace import TraceEvent, trace as _trace


def log(msg: str, layer: str = "app"):
    """通用文本日志，指定层"""
    _trace.log(msg, layer)


def app(msg: str):
    """输出到 app 层 (level=50)"""
    _trace.app(msg)


def debug(msg: str):
    """输出到 debug 层 (level=10)"""
    _trace.debug(msg)


def warning(msg: str):
    """输出到 warning 层 (level=30)"""
    _trace.warning(msg)


def error(msg: str):
    """输出到 error 层 (level=40)"""
    _trace.error(msg)


def info(msg: str):
    """输出 INFO 级别日志 (无层标签)"""
    _trace.info(msg)


# --- 属性控制 ---

def __setattr__(name, value):
    """属性控制: trace.driver = True"""
    setattr(_trace, name, value)


def __getattr__(name):
    """属性获取: trace.driver"""
    return getattr(_trace, name)


def set_layer(layer: str, enable: bool = True):
    """
    开启或关闭追踪层。

    Args:
        layer: 层级名称 ("driver", "debug", "protocol", "warning", "error", "app")
        enable: True 开启，False 关闭
    """
    _trace.set_layer(layer, enable)


def set_level(level: str):
    """
    设置最低日志级别。

    Args:
        level: 级别名称 ("trace", "debug", "warning", "error", "app")
    """
    _trace.set_level(level)


def set_parse(level: int = 1):
    """
    设置解析级别。

    Args:
        level: 0=关闭(hex), 1=简单(hex + 摘要标签)
    """
    _trace.set_parse(level)


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
