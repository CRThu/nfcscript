"""ASSERT_EQUAL / ASSERT_LEN / ASSERT_IS_NONE / ASSERT_IS_NOT_NONE 测试"""
import pytest
from nfc.assertions import (
    ASSERT_EQUAL,
    ASSERT_LEN,
    ASSERT_IS_NONE,
    ASSERT_IS_NOT_NONE,
)


class TestASSERT_EQUAL:

    def test_equal_int(self):
        ASSERT_EQUAL(42, 42)

    def test_equal_str(self):
        ASSERT_EQUAL("abc", "abc")

    def test_equal_bytes(self):
        ASSERT_EQUAL(b'\x01\x02', b'\x01\x02')

    def test_equal_list(self):
        ASSERT_EQUAL([1, 2, 3], [1, 2, 3])

    def test_not_equal_raises(self):
        with pytest.raises(AssertionError, match="Value mismatch"):
            ASSERT_EQUAL(1, 2)

    def test_custom_msg(self):
        with pytest.raises(AssertionError, match="custom message"):
            ASSERT_EQUAL(1, 2, msg="custom message")

    def test_mixed_types_raises(self):
        with pytest.raises(AssertionError):
            ASSERT_EQUAL(1, "1")

    def test_none_equal(self):
        ASSERT_EQUAL(None, None)

    def test_none_vs_value_raises(self):
        with pytest.raises((AssertionError, TypeError)):
            ASSERT_EQUAL(None, 0)


class TestASSERT_LEN:

    def test_correct_length(self):
        ASSERT_LEN([1, 2, 3], 3)

    def test_correct_length_str(self):
        ASSERT_LEN("hello", 5)

    def test_correct_length_bytes(self):
        ASSERT_LEN(b'\x01\x02', 2)

    def test_wrong_length_raises(self):
        with pytest.raises(AssertionError, match="Length mismatch"):
            ASSERT_LEN([1, 2, 3], 5)

    def test_custom_msg(self):
        with pytest.raises(AssertionError, match="wrong len"):
            ASSERT_LEN([1], 10, msg="wrong len")

    def test_zero_length(self):
        ASSERT_LEN([], 0)

    def test_zero_length_string(self):
        ASSERT_LEN("", 0)


class TestASSERT_IS_NONE:

    def test_none_passes(self):
        ASSERT_IS_NONE(None)

    def test_not_none_raises(self):
        with pytest.raises(AssertionError, match="Expected None"):
            ASSERT_IS_NONE(42)

    def test_empty_string_raises(self):
        with pytest.raises(AssertionError):
            ASSERT_IS_NONE("")

    def test_zero_raises(self):
        with pytest.raises(AssertionError):
            ASSERT_IS_NONE(0)

    def test_false_raises(self):
        with pytest.raises(AssertionError):
            ASSERT_IS_NONE(False)

    def test_custom_msg(self):
        with pytest.raises(AssertionError, match="should be none"):
            ASSERT_IS_NONE(1, msg="should be none")


class TestASSERT_IS_NOT_NONE:

    def test_value_passes(self):
        ASSERT_IS_NOT_NONE(42)

    def test_zero_passes(self):
        ASSERT_IS_NOT_NONE(0)

    def test_empty_string_passes(self):
        ASSERT_IS_NOT_NONE("")

    def test_empty_list_passes(self):
        ASSERT_IS_NOT_NONE([])

    def test_false_passes(self):
        ASSERT_IS_NOT_NONE(False)

    def test_none_raises(self):
        with pytest.raises(AssertionError, match="Expected Not None"):
            ASSERT_IS_NOT_NONE(None)

    def test_returns_true(self):
        assert ASSERT_IS_NOT_NONE("hello") is True

    def test_custom_msg(self):
        with pytest.raises(AssertionError, match="must exist"):
            ASSERT_IS_NOT_NONE(None, msg="must exist")
