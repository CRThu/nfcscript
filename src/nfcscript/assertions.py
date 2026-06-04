import inspect
from typing import Any

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

def ASSERT_LEN(data: Any, expected_len: int) -> None:
    actual_len = len(data)
    if actual_len != expected_len:
        error_msg = (
            f"\nAssertion Failed: Length mismatch\n"
            f"  Expected: {expected_len}\n"
            f"  Actual  : {actual_len}\n"
            f"  Data    : {data}\n"
            f"Stack Trace:\n{_get_stack_trace()}"
        )
        raise AssertionError(error_msg)

def ASSERT_EQUAL(actual: Any, expected: Any) -> None:
    if actual != expected:
        error_msg = (
            f"\nAssertion Failed: Value mismatch\n"
            f"  Expected: {expected} ({type(expected).__name__})\n"
            f"  Actual  : {actual} ({type(actual).__name__})\n"
            f"Stack Trace:\n{_get_stack_trace()}"
        )
        raise AssertionError(error_msg)
