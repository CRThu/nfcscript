import inspect
from typing import Any, TypeGuard, TypeVar

from nfc.hex_util import FORMAT_HEX

T = TypeVar("T")

def _get_stack_trace() -> str:
    """获取格式化的调用堆栈"""
    # inspect.stack()[0] 是 _get_stack_trace
    # inspect.stack()[1] 是 ASSERT_... 函数
    # inspect.stack()[2:] 是实际的业务调用代码
    stack = inspect.stack()[2:]
    chain = []
    for frame in stack:
        # 简化路径，仅显示文件名
        filename = frame.filename.split('\\')[-1].split('/')[-1]
        chain.append(f"  at {filename}:{frame.lineno} in {frame.function}")
    return "\n".join(chain)

def ASSERT_LEN(data: Any, expected_len: int, msg: str | None = None) -> None:
    """
    断言数据长度等于期望值。

    Args:
        data: 待检查的数据。
        expected_len: 期望的长度。
        msg: 失败时的自定义错误消息。

    Raises:
        AssertionError: 长度不匹配时抛出。
    """
    actual_len = len(data)
    if actual_len != expected_len:
        error_msg = (
            f"\nAssertion Failed: {msg}\n" if msg else ""
        ) + (
            f"Assertion Failed: Length mismatch\n"
            f"  Expected: {expected_len}\n"
            f"  Actual  : {actual_len}\n"
            f"  Data    : {data}\n"
            f"Stack Trace:\n{_get_stack_trace()}"
        )
        raise AssertionError(error_msg)

def ASSERT_EQUAL(expected: Any, actual: Any, msg: str | None = None) -> None:
    """
    断言两个值相等。

    Args:
        expected: 期望值。
        actual: 实际值。
        msg: 失败时的自定义错误消息。

    Raises:
        AssertionError: 值不相等时抛出。
    """
    if actual != expected:
        error_msg = (
            f"\nAssertion Failed: {msg}\n" if msg else ""
        ) + (
            f"Assertion Failed: Value mismatch\n"
            f"  Expected: {FORMAT_HEX(expected)} ({type(expected).__name__})\n"
            f"  Actual  : {FORMAT_HEX(actual)} ({type(actual).__name__})\n"
            f"Stack Trace:\n{_get_stack_trace()}"
        )
        raise AssertionError(error_msg)

def ASSERT_IS_NONE(value: Any, msg: str | None = None) -> None:
    """
    断言值为 None。

    Args:
        value: 待检查的值。
        msg: 失败时的自定义错误消息。

    Raises:
        AssertionError: 值不为 None 时抛出。
    """
    if value is not None:
        error_msg = (
            f"\nAssertion Failed: {msg}\n" if msg else ""
        ) + (
            f"Assertion Failed: Expected None\n"
            f"  Actual  : {value} ({type(value).__name__})\n"
            f"Stack Trace:\n{_get_stack_trace()}"
        )
        raise AssertionError(error_msg)

def ASSERT_IS_NOT_NONE(value: T | None, msg: str | None = None) -> TypeGuard[T]:
    """
    断言值不为 None。

    Args:
        value: 待检查的值。
        msg: 失败时的自定义错误消息。

    Returns:
        TypeGuard[T]: 值不为 None 时返回 True。

    Raises:
        AssertionError: 值为 None 时抛出。
    """
    if value is None:
        error_msg = (
            f"\nAssertion Failed: {msg}\n" if msg else ""
        ) + (
            f"Assertion Failed: Expected Not None\n"
            f"  Actual  : {value}\n"
            f"Stack Trace:\n{_get_stack_trace()}"
        )
        raise AssertionError(error_msg)
    return True
