from nfcscript import get_nfc, ASSERT, register
from crft.hardware.serial_transport import SerialTransport
from crft.drivers.pn532_hsu import PN532_HSU
from crft.cards.ntag21x import NTAG21x

def demo_ntag21x():
    print("--- NFC Demo: Dynamic Loading & Binding ---")
    
    # 1. 注册插件
    register("hardware", "serial", SerialTransport)
    register("driver", "pn532", PN532_HSU)
    # 注册卡片时包含 SAK 信息，用于自动探测
    register("card", "ntag21x", NTAG21x, sak=0x44) # 假设 NTAG21x SAK 为 0x44
    
    # 2. 动态拼装控制器
    nfc = get_nfc(hardware="serial", driver="pn532", port="COM20")
    
    # 3. 模式一：手动绑定
    print("模式一：手动绑定")
    nfc.bind_card("ntag21x")
    print(f"当前卡类型: {type(nfc.active_tag).__name__}")
    
    # 4. 模式二：自动探测
    print("\n模式二：自动探测")
    nfc.find_card()
    print(f"自动发现卡片: {type(nfc.active_tag).__name__}, UID={nfc.active_tag.uid.hex(' ')}")
    
    print("\n正在尝试读取卡片版本...")
    version = nfc.get_version()
    print(f"读取成功: {version.hex(' ')}")
    
    # 5. 断言
    ASSERT(len(version), 8)

if __name__ == "__main__":
    demo_ntag21x()
