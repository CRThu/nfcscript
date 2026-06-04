from .registry import get, get_name_by_sak

class NfcController:
    def __init__(self, hardware_name, driver_name, port):
        # 1. 动态加载并初始化硬件传输层
        hw_class = get("hardware", hardware_name)
        self._transport = hw_class(port=port)
        
        # 2. 动态加载并初始化驱动，并注入传输层
        drv_class = get("driver", driver_name)
        self._driver = drv_class(transport=self._transport)
        self._driver.connect()
        
        self.active_tag = None

    def bind_card(self, card_name: str, uid: bytes = b'\x00' * 7):
        """手动指定卡类型，直接绑定 (跳过物理寻卡)"""
        card_class = get("card", card_name)
        self.active_tag = card_class(reader=self._driver, uid=uid)
        return self.active_tag

    def find_card(self):
        """物理寻卡，自动匹配类型并绑定"""
        card_info = self._driver.find()
        if not card_info:
            raise RuntimeError("物理层寻卡失败")
        
        # 查找 SAK 对应名称
        card_name = get_name_by_sak(card_info.get('sak'))
        if not card_name:
            raise RuntimeError(f"未找到 SAK=0x{card_info.get('sak', 0):02X} 对应的卡片驱动")
        
        card_class = get("card", card_name)
        self.active_tag = card_class(reader=self._driver, uid=card_info["uid"])
        return self.active_tag

    def __getattr__(self, name):
        """自动转发给 active_tag"""
        if self.active_tag and hasattr(self.active_tag, name):
            return getattr(self.active_tag, name)
        raise AttributeError(f"'NfcController' has no attribute '{name}'")

    def transceive(self, data: bytes, **kwargs) -> bytes:
        """透传代理"""
        return self._driver.transceive(data, **kwargs)

    @property
    def driver(self):
        """访问底层驱动对象"""
        return self._driver
