"""cli_collect 装饰器和 _call_method 参数解析测试"""
import pytest
from nfc.nfc_cli import cli_collect, _call_method


class DummyCard:
    """模拟卡片类，用于测试"""

    def write(self, data: list[int]) -> list[int]:
        return data

    @cli_collect(key=6, uid=4)
    def mf_auth(self, block: int, key_type: int, key: list[int], uid: list[int]) -> dict:
        return {"block": block, "key_type": key_type, "key": key, "uid": uid}

    @cli_collect(key=6, uid=None)
    def mf_auth_var(self, block: int, key_type: int, key: list[int], uid: list[int]) -> dict:
        return {"block": block, "key_type": key_type, "key": key, "uid": uid}

    @cli_collect(data=None)
    def write_all(self, data: list[int]) -> list[int]:
        return data

    def read_page(self, page: int) -> list[int]:
        return [page, 1, 2, 3]

    def simple(self, a: int, b: int) -> tuple:
        return (a, b)


@pytest.fixture
def card():
    return DummyCard()


class TestFallbackPositional:
    """无装饰器，回退到最后一个参数收集剩余"""

    def test_single_param(self, card):
        result = _call_method(card.write, "01 02 03 04")
        assert result == [1, 2, 3, 4]

    def test_two_params_exact(self, card):
        result = _call_method(card.simple, "10 20")
        assert result == (10, 20)

    def test_two_params_excess(self, card):
        result = _call_method(card.simple, "10 20 30 40 50")
        assert result == (10, [20, 30, 40, 50])

    def test_one_param_exact(self, card):
        result = _call_method(card.read_page, "5")
        assert result == [5, 1, 2, 3]

    def test_no_args(self, card):
        with pytest.raises(TypeError):
            _call_method(card.write, "")


class TestCliCollectFixed:
    """cli_collect 固定长度"""

    def test_fixed_length(self, card):
        result = _call_method(card.mf_auth, "4 0 01 02 03 04 05 06 07 08 09 0x0A")
        assert result["block"] == 4
        assert result["key_type"] == 0
        assert result["key"] == [1, 2, 3, 4, 5, 6]
        assert result["uid"] == [7, 8, 9, 10]

    def test_fixed_length_short_input(self, card):
        result = _call_method(card.mf_auth, "4 0 01 02 03 04 05 06")
        assert result["block"] == 4
        assert result["key_type"] == 0
        assert result["key"] == [1, 2, 3, 4, 5, 6]
        assert result["uid"] == []


class TestCliCollectVariable:
    """cli_collect 不定长 (None)"""

    def test_variable_length(self, card):
        result = _call_method(card.mf_auth_var, "4 0 01 02 03 04 05 06 07 08 09 0x0A")
        assert result["block"] == 4
        assert result["key_type"] == 0
        assert result["key"] == [1, 2, 3, 4, 5, 6]
        assert result["uid"] == [7, 8, 9, 10]

    def test_variable_length_empty(self, card):
        result = _call_method(card.mf_auth_var, "4 0 01 02 03 04 05 06")
        assert result["block"] == 4
        assert result["key_type"] == 0
        assert result["key"] == [1, 2, 3, 4, 5, 6]
        assert result["uid"] == []


class TestCliCollectAllVariable:
    """cli_collect 单参数不定长"""

    def test_collect_all(self, card):
        result = _call_method(card.write_all, "01 02 03 04")
        assert result == [1, 2, 3, 4]

    def test_collect_empty(self, card):
        with pytest.raises(TypeError):
            _call_method(card.write_all, "")
