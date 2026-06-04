from typing import Optional
from .types import TagProtocol
from .registry import get, get_name_by_sak

class NfcReader:
    def __init__(self, hardware_name, driver_name, port):
        # 1. 动态加载并初始化硬件传输层
        hw_class = get("hardware", hardware_name)
        self._transport = hw_class(port=port)
        
        # 2. 动态加载并初始化驱动，并注入传输层
        drv_class = get("driver", driver_name)
        self._driver = drv_class(transport=self._transport)
        self._driver.connect()
        
        self.active_tag: Optional[TagProtocol] = None

    def bind_card(self, card_name: str, uid: bytes = b'\x00' * 7):
        """手动指定卡类型和 UID，直接绑定（不做物理寻卡）"""
        card_class = get("card", card_name)
        self.active_tag = card_class(reader=self._driver, uid=uid)
        self._bind_card_name = card_name
        return self.active_tag

    def find_raw(self):
        """仅物理寻卡，返回原始信息 dict（不做自动绑定）"""
        card_info = self._driver.find()
        if not card_info:
            raise RuntimeError("物理层寻卡失败")
        return card_info

    def find_card(self):
        """物理寻卡并绑定。
        - 已有 bind（active_tag 非空）→ 复用其卡类型，更新为真实 UID
        - 没有 bind                  → 从 SAK 自动猜测卡类型
        """
        card_info = self.find_raw()
        uid = card_info["uid"]

        if self.active_tag is not None and hasattr(self, "_bind_card_name"):
            card_name = self._bind_card_name
        else:
            sak = card_info.get("sak")
            card_name = get_name_by_sak(sak)
            if not card_name:
                raise RuntimeError(f"未找到 SAK=0x{sak:02X} 对应的卡片驱动")

        card_class = get("card", card_name)
        self.active_tag = card_class(reader=self._driver, uid=uid)
        return self.active_tag

    def __getattr__(self, name):
        """自动转发给 active_tag"""
        if self.active_tag and hasattr(self.active_tag, name):
            return getattr(self.active_tag, name)
        raise AttributeError(f"'NfcReader' has no attribute '{name}'")

    def transceive(self, data: bytes, **kwargs) -> bytes:
        """透传代理"""
        return self._driver.transceive(data, **kwargs)

    @property
    def driver(self):
        """访问底层驱动对象"""
        return self._driver
