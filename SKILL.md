---
name: nfcscript
description: 使用 nfcscript DSL 生成 NFC 测试脚本和卡片驱动。当用户需要编写 NFC 测试脚本、创建自定义卡片实现、实现卡片协议、或使用 nfctester/nfcscript 框架时触发。
---

# nfcscript DSL

所有函数通过 `from nfc import *` 导入。运行：`nfcscript <script.py> -p COM21 -r pn532`。
环境变量：`NFC_PORT`、`NFC_READER`、`NFC_TRACE_LAYER`、`NFC_TRACE_LEVEL`。

## API

### 读卡器单例 (`reader`)

支持从 `.env` 自动注入环境变量 `NFC_PORT` 与 `NFC_READER`，首次操作自动连接，退出自动关闭 RF 与串口：

```python
from nfc import reader

# 1. 射频场控制
reader.rf = True          # 开启 RF 场 (或 reader.field_on())
reader.rf = False         # 关闭 RF 场 (或 reader.field_off())

# 2. 寻卡激活
card = reader.active(low_layer=False, ignore_error=False, reqa_cmd=0x26)
# 返回 CardInfo(uid: list[int], atq: list[int], sak: int) 或 None
# low_layer=True: 手动底层寻卡流程（兼容非标卡）；reqa_cmd 仅 low_layer=True 时生效

# 3. ISO14443-A 底层指令
reader.reqa(cmd=0x26)     # REQA（7-bit 短帧），返回 TransceiveBits
reader.wupa()             # WUPA，返回 TransceiveBits
reader.halt()             # HALT
reader.select(cl_level, uid)                # uid: 5-byte list（含 BCC）
reader.anticoll(cl_level, nvb=0x20, uid_prefix=[])  # 返回 TransceiveBits

# 4. 手动控制 (可选)
reader.connect(port=None, reader_type=None)  # 显式连接（默认自动按需连接）
reader.close()                               # 显式断开（退出时 atexit 自动清理）
with reader.session(port="COM21", reader_type="pn532"): ... # 局部会话
```

### 数据收发

```python
res = reader.transceive(data, tx_crc=True, rx_crc=True)
# data: list[int] | bytes，返回 list[int]（空列表表示失败）
# tx_crc/rx_crc=False 时原样收发，不加/不校验 CRC

res_bits = reader.transceive_bits(data, last_tx_bits=0, tx_crc=True, rx_crc=True)
# 返回 TransceiveBits (失败时 data=[])
# TransceiveBits: .data: list[int], .bits: int
# tx_crc/rx_crc=False 时原样收发，不加/不校验 CRC
```

### 断言

```python
ASSERT_EQUAL(expected, actual, msg=None)   # expected 在前
ASSERT_LEN(data, expected_len, msg=None)
ASSERT_IS_NOT_NONE(value, msg=None)
ASSERT_IS_NONE(value, msg=None)
```

### 工具

```python
FORMAT_HEX(data, last_bits=0)   # "AA BB 7'h03"
PARSE_HEX(text)                  # [0xAA, 0xBB, 0xCC]
PARSE_HEX_BITS(text, last_bits=None)  # ([0xAA, 0x0B], 4)
BITS_UPDATE(val, mask, data)     # 读-改-写
BITS_SET(val, mask)
BITS_RESET(val, mask)
GET_BCC(data)                    # 异或校验
DELAY_MS(ms)
```

### trace 日志

```python
# 简洁写法（推荐）
trace.app("UID: AA BB CC DD")                  # app 层输出
trace.debug("[auth] Rt: 80 81")                # debug 层输出
trace.warning("Low battery")                   # warning 层
trace.error("Connection failed")               # error 层

# 属性控制（推荐）
trace.filter.driver = True                     # 开启 driver 层
trace.filter.protocol = True                   # 开启 protocol 层
trace.filter.debug = False                     # 关闭 debug 层
trace.filter.level = "warning"                 # 最低级别过滤
trace.filter.level = 30                        # 或数字

# 统一入口
trace.log("msg", layer="app")                  # 通用文本日志，指定层

# 方法
trace.set_parse(1)                             # 0=关闭, 1=简单
```

## Few-shot

### 基础脚本：寻卡 + 读数据

```python
from nfc import *

connect()
field_on()

card_info = active(low_layer=True, ignore_error=True)
ASSERT_IS_NOT_NONE(card_info, "未扫描到卡片")
trace.app(f"UID: {FORMAT_HEX(card_info.uid)}")
trace.app(f"ATQ: {FORMAT_HEX(card_info.atq)}  SAK: 0x{card_info.sak:02X}")

resp = transceive([0x30, 0x00])  # READ page 0
ASSERT_EQUAL(16, len(resp), "响应长度错误")
trace.app(f"Data: {FORMAT_HEX(resp)}")

field_off()
close()
```

### 位级别收发（transceive_bits）

```python
from nfc import *

connect()
field_on()

card_info = active(low_layer=True, ignore_error=True)
ASSERT_IS_NOT_NONE(card_info, "未扫描到卡片")

# 4-bit ACK 场景：关闭 rx_crc，检查 bits
result = transceive_bits([0xA0, 0x00], tx_crc=True, rx_crc=False)
ASSERT_IS_NOT_NONE(result, "transceive 失败")
ASSERT_EQUAL(4, result.bits, "ACK 位数错误")
ASSERT_EQUAL([0x0A], result.data, "NAK")

DELAY_MS(1)

result = transceive_bits([0xAA] * 16, tx_crc=True, rx_crc=False)
ASSERT_IS_NOT_NONE(result, "transceive 失败")
ASSERT_EQUAL([0x0A], result.data, "数据 NAK")

field_off()
close()
```

### 自定义卡片驱动

简单标签继承 `BaseTag`，加密卡继承 `BaseCard`：

```python
from nfc import *
from nfctester.cards import BaseTag, BaseCard

class MyTag(BaseTag):
    def __init__(self, reader):
        super().__init__(reader)

    def read_page(self, page):
        return self.transceive(bytes([0x30, page]))

    def write_page(self, page, data):
        return self.transceive(bytes([0xA2, page]) + data)

# 使用
card = MyTag(get_reader())
data = card.read_page(0x04)
card.write_page(0x04, b'\x01' * 4)
```

```python
from nfc import *
from nfctester.registry import CardRegistry
from nfctester.cards import BaseCard

@CardRegistry.register("my_card")
class MyCard(BaseCard):
    def __init__(self, reader):
        super().__init__(reader)

    def authenticate(self, block_addr, key, key_type):
        # 实现认证逻辑
        pass

    def read_block(self, block_addr):
        return self.transceive(bytes([0x30, block_addr]))

    def write_block(self, block_addr, data):
        return self.transceive(bytes([0xA2, block_addr]) + data)

# 脚本中使用
card = CardRegistry.create("my_card", reader=get_reader())
card.authenticate(7, bytes.fromhex("FFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFF"), 0x60)
data = card.read_block(8)
```

## 关键约定

- 数据类型：DSL 函数用 `list[int]`；Card 类方法用 `bytes`
- `active()` 返回 `CardInfo` 对象（`.uid`, `.atq`, `.sak`），不是 raw list
- `transceive_bits()` 失败返回 `None`，使用前需检查
- `get_reader()` 传给自定义 Card 构造函数，不直接用于 DSL 操作
- 脚本固定结构：`connect()` → `field_on()` → ... → `field_off()` → `close()`
- `BaseTag` 从 `nfctester.cards` 导入；`BaseCard` 同理
- 注册卡片：`@CardRegistry.register("name")` 装饰器，`from nfctester.registry import CardRegistry`
- **禁止删除现有注释**：脚本可能存在被注释的情况，除非明确确认无用，否则不得删除

### trace 层控制完整示例

```python
# 属性控制
trace.filter.driver = True    # 启用 driver 层
trace.filter.protocol = True  # 启用 protocol 层
trace.filter.debug = False    # 禁用 debug 层
trace.filter.level = "debug"  # 设置最低级别

# 输出日志
trace.app("业务输出")
trace.debug("调试信息")
trace.warning("警告信息")
trace.error("错误信息")
```
