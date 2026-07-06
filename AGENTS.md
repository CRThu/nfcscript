# AGENTS.md: nfcscript 项目架构说明书 (AI 专用)

## 1. 项目概述
`nfcscript` 是一个轻量级 NFC 测试 DSL 执行环境。它**复用** `nfctester` 的 Registry 插件化架构，提供简洁的模块级函数接口，让测试脚本无需关心底层硬件和驱动的创建细节。

## 2. 架构设计

nfcscript **不实现**自己的 Registry，而是直接使用 `nfctester.registry` 中的：
- `TransportRegistry` - 传输层注册表
- `CardReaderRegistry` - 读卡器注册表
- `CardRegistry` - 卡片注册表

导入 `nfctester` 时，其 `__init__.py` 会自动导入所有卡片类（带 `@CardRegistry.register()` 装饰器），完成内置组件的注册。

## 3. 核心组件 (src/nfc/)

### `reader.py`: 全局函数接口
提供模块级函数，封装底层 nfctester 操作：

*   `connect(port=None, reader_type=None)`: 通过 `CardReaderRegistry.create()` 创建并连接读卡器。默认从环境变量 `NFC_PORT` / `NFC_READER` 读取。
*   `get_reader()`: 获取当前连接的读卡器实例，供 Card 类使用。
*   `active(low_layer=False, ignore_error=False, reqa_cmd=0x26)`: 寻卡，返回 `CardInfo | None`（含 `uid`, `atq`, `sak`）。`low_layer=True` 由 nfcscript 执行底层抗冲突流程，`reqa_cmd` 仅 `low_layer=True` 时生效。
*   `transceive(data, tx_crc=True, rx_crc=True)`: 底层帧交互。`tx_crc=False`/`rx_crc=False` 时原样收发不加/不校验 CRC。
*   `transceive_bits(data, last_tx_bits=0, tx_crc=True, rx_crc=True)`: 支持位控制的帧交互，返回 `TransceiveBits | None` (含 `.data` 和 `.bits` 属性)。`tx_crc=False`/`rx_crc=False` 时原样收发不加/不校验 CRC。
*   `reqa(cmd=0x26)`: ISO14443-A REQA 短帧命令。
*   `wupa()`: ISO14443-A WUPA 短帧命令。
*   `halt()`: ISO14443-A HALT 命令。
*   `select(cl_level, uid)`: ISO14443-A SELECT。
*   `anticoll(cl_level, nvb=0x20, uid_prefix=[])`: ISO14443-A ANTICOLL。
*   `field_on()` / `field_off()`: RF 场控制。
*   `session(port=None, reader_type=None)`: 上下文管理器，自动管理连接生命周期。
*   `close()`: 断开连接。

### `trace.py`: 日志追踪模块
包装 `nfctester.trace`，提供日志控制功能：

*   `trace.set_layer(layer, enable)`: 开启/关闭追踪层 ("DRIVER", "PROTOCOL")。
*   `trace.set_level(level)`: 设置日志级别 ("INFO", "DEBUG", "ERROR")。
*   `trace.set_parse(level=1)`: 设置解析级别 (0=关闭, 1=简单, 2=树状结构)。
*   `trace.set_card_type(card_type)`: 设置卡片类型标识，注入到协议解析器。
*   `trace.info(msg)` / `trace.error(msg)` / `trace.warning(msg)` / `trace.success(msg)` / `trace.debug(msg)`: 输出日志。

### `__init__.py`: 模块入口
导入所有子模块，自动导出公共函数。通过 `from nfc import *` 可导入全部工具，包括 `trace` 模块。

### `assertions.py`: 测试断言工具
*   `ASSERT_EQUAL(expected, actual, msg=None)`: 相等断言。
*   `ASSERT_LEN(data, expected_len, msg=None)`: 长度断言。
*   `ASSERT_IS_NOT_NONE(value, msg=None)`: 非空断言。
*   `ASSERT_IS_NONE(value, msg=None)`: 空值断言。

### `bits.py`: 位操作工具
*   `BITS_UPDATE(val, mask, data)`: Read-Modify-Write。
*   `BITS_SET(val, mask)`: 置位。
*   `BITS_RESET(val, mask)`: 清位。

### `hex_util.py`: 十六进制工具
*   `PARSE_HEX(text)`: 解析带位标记的 hex 字符串。
*   `FORMAT_HEX(data, last_bits=0)`: 格式化为可视化 hex。

### `checksum.py`: 校验工具
*   `GET_BCC(data)`: 计算异或校验。

### `delay.py`: 延时工具
*   `DELAY_MS(ms)`: 毫秒延时。

### `cli.py`: CLI 入口
命令行入口，支持以下参数：
*   `nfcscript <script_path>`: 运行脚本。
*   `-p, --port`: 指定串口号 (必须通过参数、环境变量或 `.env` 配置)。
*   `-r, --reader`: 指定读卡器类型 (必须通过参数、环境变量或 `.env` 配置)。
*   `--trace-driver`: 开启 DRIVER 层追踪。
*   `--trace-protocol`: 开启 PROTOCOL 层追踪。
*   `--trace-parse`: 解析级别 (0=关闭, 1=简单, 2=树状)。
*   `--trace-card-type`: 卡片类型标识，注入到协议解析器。
*   `--trace-level`: 设置日志级别 (默认: INFO)。

环境变量优先级: CLI 参数 > 内层 `.env` > 外层 `.env` > 系统环境变量 > 硬编码默认值。

支持多层 `.env` 加载：从脚本目录向上搜索所有 `.env` 文件，按从外到内的顺序依次加载（内层覆盖外层同名变量）。

| 变量 | 说明 | 默认值 |
|------|------|--------|
| `NFC_PORT` | 串口号 | - |
| `NFC_READER` | 读卡器类型 | - |
| `NFC_TRACE_LEVEL` | 日志级别 | `INFO` |
| `NFC_TRACE_DRIVER` | 开启 DRIVER 层追踪 | `false` |
| `NFC_TRACE_PROTOCOL` | 开启 PROTOCOL 层追踪 | `false` |
| `NFC_TRACE_PARSE` | 解析级别 | `1` |
| `NFC_TRACE_CARD_TYPE` | 卡片类型标识 | - |
| `NFC_TRACE_WIDTH` | 输出宽度 | - |

### `nfc_cli.py`: 交互式卡片 CLI
卡片交互式命令行工具，支持 `@cli_collect` 装饰器标记 list 参数。

```python
from nfc.nfc_cli import cli_collect

@cli_collect(key=6, uid=4)    # key 固定 6 字节，uid 固定 4 字节
def mf_auth(self, block, key_type, key, uid): ...

@cli_collect(data=None)        # data 不定长，收集剩余参数
def write(self, data): ...
```

*   固定长度：`@cli_collect(key=6)` — 精确收集 6 个值
*   不定长：`@cli_collect(data=None)` — 收集所有剩余值
*   无装饰器：回退到最后一个参数自动收集多余值

CLI 调用示例：
```
> mf_auth 4 0 01 02 03 04 05 06 07 08 09 0A
# → block=4, key_type=0, key=[1..6], uid=[7..10]
> write 01 02 03 04
# → data=[1,2,3,4]
```

## 4. 依赖关系

```
nfcscript
    └── nfctester (workspace 依赖)
            ├── registry (TransportRegistry, CardReaderRegistry, CardRegistry)
            ├── hardware (SerialTransport)
            ├── drivers (PN532_HSU)
            ├── cards (NTAG21x, NTAG224, MifareClassicCard, Type2Tag)
            └── trace (TraceManager, loguru)
```

## 5. 开发规范

*   **复用 nfctester Registry**: 新增卡片/驱动应在 nfctester 中通过 `@CardRegistry.register()` 注册，nfcscript 自动继承。
*   **严禁硬编码**: 不直接 `import` 具体的 Transport/Driver/Card 类，通过 Registry 动态获取。
*   **Tooling**: 所有操作使用 `uv` 工具链。

## 6. AI 编写脚本指南

本目录下 `SKILL.md` 是给 AI Agent（如 Codex、MiMo Code 等）的 DSL 使用手册，包含：
- 完整 API 签名与说明
- Few-shot 示例（基础脚本、位级别收发、自定义卡片驱动）
- 关键约定（数据类型、返回值、脚本结构）

**使用方式**：在对话中引用此文件，让 Agent 生成符合规范的脚本：
- `@nfcscript/SKILL.md` — 将 skill 注入 Agent 上下文
- Agent 会基于 API 参考和 few-shot 生成正确的 `from nfc import *` 脚本

## 7. 调试指南
*   检查注册表: `from nfctester.registry import CardRegistry; print(CardRegistry.list())`
*   检查连接: `connect()` 后检查 `_reader` 是否为 `None`。
*   开启追踪: 使用 CLI 参数 `--trace-driver --trace-protocol` 或在脚本中调用 `trace.set_layer()`。
*   通信日志: 由底层 `nfctester.trace` 模块处理，支持 DRIVER 和 PROTOCOL 两层。

---
*保持架构简单。nfcscript 是 nfctester 的 DSL 薄封装层，不是独立的插件系统。*
