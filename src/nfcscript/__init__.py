from .wrapper import NfcController
from .assertions import ASSERT_EQUAL as ASSERT
from .registry import register, get

_controllers = {}

def get_nfc(id="default", hardware="serial", driver="pn532", port="COM20"):
    """
    获取或创建 NFC 控制器，通过硬件层和驱动层名称动态拼装。
    """
    if id not in _controllers:
        _controllers[id] = NfcController(hardware_name=hardware, driver_name=driver, port=port)
    return _controllers[id]
