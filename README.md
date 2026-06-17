# nfcscript

NFC 测试脚本 DSL 执行环境，基于 `nfctester` 插件化架构。

## 安装

```bash
uv sync
```

## 使用

### 基本用法

```bash
nfcscript test_card.py
```

### 常用参数

```bash
# 指定串口
nfcscript test_card.py -p COM21

# 指定读卡器类型
nfcscript test_card.py -r acr122u

# 开启追踪层
nfcscript test_card.py --trace-driver --trace-protocol

# 设置日志级别
nfcscript test_card.py --trace-level DEBUG

# 组合使用
nfcscript test_card.py -p COM21 -r pn532 --trace-driver --trace-protocol --trace-level DEBUG
```

### 脚本示例

```python
from nfc import *

# 连接读卡器 (默认使用环境变量 NFC_PORT 或 COM20)
connect()

# 开启追踪
trace.set_layer("DRIVER", True)
trace.set_layer("PROTOCOL", True)

# 寻卡
card_info = active()
ASSERT_IS_NOT_NONE(card_info, "未扫描到卡片")
print(f"UID: {card_info['uid'].hex().upper()}")

# 创建卡片实例
from nfctester.registry import CardRegistry
card = CardRegistry.create("mifare", reader=get_reader())

# 关闭连接
close()
```

### 上下文管理器

```python
from nfc import *

with session() as reader:
    card_info = reader.find()
    print(card_info)
# 自动断开连接
```

## 模块说明

| 模块 | 说明 |
|------|------|
| `reader.py` | 读卡器连接与通信 |
| `trace.py` | 日志追踪控制 |
| `assertions.py` | 测试断言 |
| `bits.py` | 位操作工具 |
| `hex_util.py` | 十六进制工具 |
| `checksum.py` | 校验工具 |
| `delay.py` | 延时工具 |

## 环境变量

| 变量 | 说明 | 默认值 |
|------|------|--------|
| `NFC_PORT` | 串口号 | `COM20` |
| `NFC_READER` | 读卡器类型 | `pn532` |

## 开发

```bash
# 运行测试
uv run pytest

# 运行特定测试
uv run pytest tests/test_xxx.py
```
