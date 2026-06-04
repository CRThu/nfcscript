import types as _types

from .reader import NfcReader
from .assertions import ASSERT_EQUAL as ASSERT
from .registry import register, get
from . import builtins
from .dsl import init_nfc, _get_controller


def _make_wrapper(name):
    """创建一个转发到 _get_controller().{name} 的真实函数/属性"""
    def _fn(*args, **kwargs):
        attr = getattr(_get_controller(), name)
        if callable(attr):
            return attr(*args, **kwargs)
        return attr
    _fn.__name__ = name
    _fn.__qualname__ = name
    return _fn


# --- 自动发现 NfcReader 公开方法 ---
for _name in dir(NfcReader):
    if not _name.startswith("_"):
        globals()[_name] = _make_wrapper(_name)

# --- 卡片常用方法（通过 NfcReader.__getattr__ 转发到 active_tag）---
for _name in ["get_version", "read", "write", "fast_read", "fast_write", "get_uid", "get_sig"]:
    globals()[_name] = _make_wrapper(_name)


# --- active_tag 也返回真实对象 ---
def get_active_tag():
    """获取当前绑定的标签对象"""
    return _get_controller().active_tag


# --- 构建 __all__：排除子模块和内部名称 ---
__all__ = [
    n for n in globals()
    if not n.startswith("_")
    and not isinstance(globals()[n], _types.ModuleType)
]
