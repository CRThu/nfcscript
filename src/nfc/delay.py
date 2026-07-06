import time

def DELAY_MS(ms: int) -> None:
    """毫秒级延时。

    Args:
        ms: 延时毫秒数。
    """
    time.sleep(ms / 1000.0)