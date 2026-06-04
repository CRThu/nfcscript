from .reader import NfcReader
from .registry import _REGISTRY

_default_controller = None


def _dump_init_info(hardware, driver, port):
    """打印各层注册信息，帮助诊断 init 链路"""
    from crft import trace as _trace

    _trace.info("=== nfcscript 初始化诊断 ===")
    _trace.info(f"请求: hardware={hardware!r}, driver={driver!r}, port={port!r}")

    # 1. 已注册的硬件传输层
    _trace.info("--- Hardware 层 ---")
    for name, klass in _REGISTRY["hardware"].items():
        _trace.info(f"  + {name}: {klass.__module__}.{klass.__name__}")

    # 2. 已注册的驱动层
    _trace.info("--- Driver 层 ---")
    for name, klass in _REGISTRY["driver"].items():
        _trace.info(f"  + {name}: {klass.__module__}.{klass.__name__}")

    # 3. 已注册的卡片层
    _trace.info("--- Card 层 ---")
    for name, klass in _REGISTRY["card"].items():
        _trace.info(f"  + {name}: {klass.__module__}.{klass.__name__}")

    # 4. SAK 映射
    _trace.info("--- SAK 映射 ---")
    for sak, name in _REGISTRY["card_sak"].items():
        _trace.info(f"  + SAK=0x{sak:02X} → {name}")

    # 5. NfcReader 的公开方法/属性
    _trace.info("--- NfcReader 公开成员 ---")
    for name in dir(NfcReader):
        if not name.startswith("_"):
            member = getattr(NfcReader, name)
            _trace.info(f"  + {name}: {type(member).__name__}")

    _trace.info("=== 诊断结束 ===")


def init_nfc(hardware="serial", driver="pn532", port="COM20"):
    """初始化全局 NFC 读卡器"""
    global _default_controller

    #_dump_init_info(hardware, driver, port)

    _default_controller = NfcReader(hardware_name=hardware, driver_name=driver, port=port)

    # 5. init 完成后再次报告 active_tag 状态
    from crft import trace as _trace
    _trace.success("NfcReader 初始化完成")
    _trace.info(f"  active_tag = {_default_controller.active_tag!r}")
    if _default_controller.active_tag:
        _trace.info(f"  active_tag 类型: {type(_default_controller.active_tag).__name__}")
        _trace.info(f"  active_tag 方法:")
        for name in dir(_default_controller.active_tag):
            if not name.startswith("_"):
                _trace.info(f"    - {name}")

    return _default_controller


def _get_controller():
    """获取当前默认控制器"""
    if _default_controller is None:
        raise RuntimeError("NFC 控制器未初始化，请先调用 init_nfc()")
    return _default_controller
