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
