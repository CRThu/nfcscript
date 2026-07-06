"""DELAY_MS 测试"""
import time
from nfc.delay import DELAY_MS


class TestDELAY_MS:

    def test_zero_ms(self):
        start = time.monotonic()
        DELAY_MS(0)
        elapsed = time.monotonic() - start
        assert elapsed < 0.05

    def test_positive_ms(self):
        start = time.monotonic()
        DELAY_MS(10)
        elapsed = time.monotonic() - start
        assert elapsed >= 0.008

    def test_returns_none(self):
        result = DELAY_MS(1)
        assert result is None
