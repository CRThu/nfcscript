# nfcscript

NFC 测试脚本 DSL 执行环境，基于 `nfctester` 插件化架构。

## 安装

```bash
uv sync
```

## 使用

### nfcscript - 脚本执行

```bash
nfcscript test_card.py
```

#### 常用参数

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

### nfc-cli - 交互式命令行

```bash
# 列出所有可用卡片类型
nfc-cli --list-cards

# 连接卡片并进入交互模式
nfc-cli -c ntag224 -p COM21

# 指定读卡器类型
nfc-cli -c mifare_classic -p COM21 -r pn532

# 通过环境变量自动发现外部卡片
export NFC_CARD_PATH="../scripts/lib"
nfc-cli -c sm7 -p COM20

# 或手动指定
nfc-cli -c sm7 -p COM20 -i ../scripts/lib
```

#### 交互命令

进入交互模式后，可以输入命令操作卡片：

```
> help              # 显示可用命令
> auth 7 FFFFFFFFFFFF  # 认证块 7
> read 10           # 读取页 10
> write 20 AABBCCDD... # 写入页 20
> quit              # 退出
```

支持的值格式：
- 十六进制: `0xFF`, `0xAABBCCDD`
- 十进制: `7`, `255`
- 字节串: `b'\xff\x00'`

#### 导入外部卡片

使用 `-i` 参数导入外部卡片模块，支持单个 `.py` 文件或包含 `__init__.py` 的目录：

```bash
# 导入单个文件
nfc-cli -c my_card -p COM20 -i /path/to/my_card.py

# 导入目录（需要有 __init__.py）
nfc-cli -c sm7 -p COM20 -i /path/to/lib
```

外部卡片模块需要使用 `@CardRegistry.register("name")` 装饰器注册。

#### 示例

```bash
# NTAG224 认证并读取
nfc-cli -c ntag224 -p COM21
> auth 1 AABBCCDD112233445566778899001122
> read 4

# Mifare Classic 操作
nfc-cli -c mifare_classic -p COM21
> authenticate 7 FFFFFFFFFFFF
> read_block 8
> write_block 9 AABBCCDD112233445566778899001122
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

## API 参考

### reader.py

| 函数 | 说明 |
|------|------|
| `connect(port, reader_type)` | 连接读卡器 |
| `get_reader()` | 获取当前读卡器实例 |
| `active(low_layer, ignore_error, reqa_cmd)` | 寻卡，返回 uid/atq/sak |
| `transceive(data, tx_crc, rx_crc)` | 底层帧交互 |
| `transceive_bits(data, last_tx_bits, tx_crc, rx_crc)` | 位控制帧交互 |
| `reqa()` | ISO14443-A REQA |
| `wupa()` | ISO14443-A WUPA |
| `halt()` | ISO14443-A HALT |
| `select(cl_level, uid)` | ISO14443-A SELECT |
| `anticoll(cl_level, nvb, uid_prefix)` | ISO14443-A ANTICOLL |
| `field_on()` / `field_off()` | RF 场控制 |
| `session(port, reader_type)` | 上下文管理器 |
| `close()` | 断开连接 |

### trace.py

| 函数 | 说明 |
|------|------|
| `trace.set_layer(layer, enable)` | 开启/关闭追踪层 |
| `trace.set_level(level)` | 设置日志级别 |
| `trace.info(msg)` / `trace.error(msg)` / `trace.warning(msg)` / `trace.success(msg)` / `trace.debug(msg)` | 输出日志 |

### assertions.py

| 函数 | 说明 |
|------|------|
| `ASSERT_EQUAL(expected, actual, msg)` | 相等断言 |
| `ASSERT_LEN(data, expected_len, msg)` | 长度断言 |
| `ASSERT_IS_NOT_NONE(value, msg)` | 非空断言 |
| `ASSERT_IS_NONE(value, msg)` | 空值断言 |

### bits.py

| 函数 | 说明 |
|------|------|
| `BITS_UPDATE(val, mask, data)` | Read-Modify-Write |
| `BITS_SET(val, mask)` | 置位 |
| `BITS_RESET(val, mask)` | 清位 |

### hex_util.py

| 函数 | 说明 |
|------|------|
| `PARSE_HEX(text)` | 解析 hex 字符串 |
| `FORMAT_HEX(data, last_bits)` | 格式化为可视化 hex |

### checksum.py

| 函数 | 说明 |
|------|------|
| `GET_BCC(data)` | 计算异或校验 |

### delay.py

| 函数 | 说明 |
|------|------|
| `DELAY_MS(ms)` | 毫秒延时 |

## 环境变量

优先级: CLI 参数 > 内层 `.env` > 外层 `.env` > 系统环境变量 (必须配置，否则报错)

| 变量 | 说明 | 默认值 |
|------|------|--------|
| `NFC_PORT` | 串口号 | - |
| `NFC_READER` | 读卡器类型 | - |
| `NFC_TRACE_LEVEL` | 日志级别 | `INFO` |
| `NFC_TRACE_DRIVER` | 开启 DRIVER 层追踪 | `false` |
| `NFC_TRACE_PROTOCOL` | 开启 PROTOCOL 层追踪 | `false` |
| `NFC_CARD_PATH` | 外部卡片模块搜索路径 (分号分隔) | - |

支持多层 `.env` 加载：从脚本目录向上搜索所有 `.env` 文件，按从外到内的顺序依次加载（内层覆盖外层同名变量）。

例如，脚本位于 `/project/tests/run.py`，沿途有 `/project/.env` 和 `/project/tests/.env`，加载顺序为：

1. `/project/.env` (基础配置)
2. `/project/tests/.env` (覆盖基础配置中的同名变量)

在项目根目录或脚本所在目录创建 `.env` 文件进行持久化配置：

```
NFC_PORT=COM20
NFC_READER=pn532
NFC_TRACE_LEVEL=DEBUG
NFC_TRACE_DRIVER=true
NFC_TRACE_PROTOCOL=true
```

## AI 编写脚本

本目录下 `SKILL.md` 提供了 DSL 的完整 API 参考和 few-shot 示例，可直接用于 AI Agent 生成 NFC 脚本。

**使用方式**：在 AI 对话中引用该文件，例如：
```
@nfcscript/SKILL.md
```
Agent 会基于 SKILL.md 中的 API 签名、few-shot 示例和约定生成正确的脚本代码。

## 开发

```bash
# 运行测试
uv run pytest

# 运行特定测试
uv run pytest tests/test_xxx.py
```
