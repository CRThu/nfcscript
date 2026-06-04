# AGENTS.md: nfcscript 项目架构说明书 (AI 专用)

## 1. 项目概述
`nfcscript` 是一个轻量级、完全插件化的 NFC 测试核心引擎。它不依赖于任何具体的硬件驱动，而是作为**插件加载器 (Plugin Loader)** 和 **DSL 执行环境**，将底层的 `CarrotRFIDTester` (crft) 逻辑封装为简洁的自动化测试接口。

## 2. 架构设计：三层动态插件模式
本项目遵循"解耦"原则，硬件、驱动与卡片逻辑均支持动态注册与加载，实现零硬编码耦合。

*   **Hardware Layer (传输层)**: 负责物理通信 (如 `SerialTransport`)。
*   **Driver Layer (协议层)**: 负责硬件读写指令处理 (如 `PN532_HSU`)。
*   **Card Layer (业务层)**: 负责卡片内部指令集与逻辑 (如 `NTAG21x`)。

## 3. 核心组件 (src/nfcscript/)

### `registry.py`: 注册中心
所有插件必须通过 `register(category, name, klass, sak=None)` 进行注册。
*   **Categories**: `hardware`, `driver`, `card`。
*   **`card_sak`**: 通过 `sak` (Select Acknowledge) 映射卡片驱动，用于自动寻卡猜测类型。
*   SAK 值: NTAG21x 系列为 `0x00`（不是 `0x44`）。
*   **`get(category, name)`**: 按分类和名称获取已注册的插件类，未找到时抛出 `ValueError`。
*   **`get_name_by_sak(sak)`**: 通过 SAK 值获取卡片名称，无匹配时返回 `None`。

### `reader.py`: NfcReader (外观模式)
引擎的核心 Orchestrator。

*   **职责**: 动态拼装传输层和驱动层，持有当前的 `active_tag` 对象。
*   **`__getattr__` 转发**: 将对 `NfcReader` 的属性访问（如 `get_version`）自动转发给当前绑定的 `active_tag`。若 `active_tag` 为 `None` 或无此属性则抛出 `AttributeError`。
*   **`transceive(data, **kwargs) -> bytes`**: 透传代理，直接转发给底层 `driver.transceive()`。
*   **`driver` property**: 访问底层驱动对象。
*   **`active_tag` attribute**: 当前绑定的卡片对象，类型为 `Optional[TagProtocol]`。
*   **双模式绑定**:
    *   `bind_card(name, uid)` → 手动指定卡类型和 UID，直接绑定（不做物理寻卡）。若后续调用 `find_card()` 会复用此类型，忽略 SAK。
    *   `find_card()` → 物理寻卡并绑定。若已有 `active_tag`（来自 `bind_card`），**复用其卡类型**并更新为真实 UID；否则从 SAK 自动猜测。
    *   `find_raw()` → 仅物理寻卡，返回原始 `dict`（含 `uid`、`sak`），不做任何绑定。寻卡失败时抛出 `RuntimeError`。
*   `_bind_card_name`: 内部属性，记录 `bind_card` 指定的卡类型名，供 `find_card` 复用。

### `dsl.py`: 控制器管理
*   `init_nfc(hardware, driver, port)`: 初始化全局 NFC 读卡器，创建 `NfcReader` 实例。支持自定义硬件/驱动/端口，`port` 默认 `"COM20"`。
*   `_get_controller()`: 内部函数，返回当前单例控制器。未初始化时抛出 `RuntimeError`。
*   `_dump_init_info()`: 每次 init 自动打印诊断信息（注册表、NfcReader 公开成员）。初始化完成后额外打印 `active_tag` 状态、类型和可用方法。

### `__init__.py`: DSL 入口 & 自动导出
*   **`_make_wrapper(name)`**: 创建真实转发函数。调用时 `_get_controller()` 获取控制器，再 `getattr` 获取实际属性。若属性是 callable（方法）则调用，否则直接返回值（支持 `@property`）。
*   **导入时自动发现** `NfcReader` 的所有公开方法（`dir(NfcReader)`），调用 `_make_wrapper` 创建真实函数并注入模块命名空间。
*   预置卡片常用方法（走 `NfcReader.__getattr__` 转发到 `active_tag`）: `get_version`, `read`, `write`, `fast_read`, `fast_write`, `get_uid`, `get_sig`。
*   `get_active_tag()`: 真实函数，返回 `_get_controller().active_tag` 真实卡片对象。
*   `ASSERT`: 从 `.assertions` 导入的 `ASSERT_EQUAL`（别名），用于测试断言。
*   `__all__` 自动构建（排除子模块），确保 `from nfcscript import *` 导入全部 DSL 名称。
*   **没有懒加载、没有代理类、没有 `__getattr__` 钩子**——全部是真实的 Python 函数。
*   **新方法加到 `NfcReader` 后自动生效**，无需修改 DSL 层。

### `.pyi` 类型存根
*   `__init__.pyi`: 声明所有 `_make_wrapper` 导出的函数签名，包括 NfcReader 方法、属性转发方法、卡片转发方法、`get_active_tag`、`ASSERT`。
*   `reader.pyi`: 声明 `NfcReader` 类的完整接口，含 `find_raw()`、`transceive()`、`driver` property。
*   `types.pyi`: `TagProtocol`（`get_version`, `read_data`, `write_data`）和 `ReaderProtocol`。

### `assertions.py`: 测试断言工具
*   `ASSERT_EQUAL(actual, expected)`: 检查两个值是否相等，不等时抛出格式化 `AssertionError`（含堆栈追踪）。
*   `ASSERT_LEN(data, expected_len)`: 检查数据长度是否匹配，不匹配时抛出格式化 `AssertionError`（含堆栈追踪）。
*   堆栈追踪自动跳过断言函数本身，指向业务调用点。

### `bits.py`: 位操作工具
*   `bits_update(val, mask, data)`: 更新寄存器中的特定位域（Read-Modify-Write）。
*   `bits_set(val, mask)`: 将寄存器中的指定位强制置 1。
*   `bits_reset(val, mask)`: 将寄存器中的指定位强制清 0。

### `main.py`: CLI 入口
*   命令行入口 `nfcscript <script_path>`，通过 `runpy.run_path(script_path, run_name="__main__")` 执行指定脚本，确保脚本内的 `if __name__ == "__main__":` 守卫正常工作。
*   将脚本所在目录加入 `sys.path` 以便脚本导入依赖。

## 4. 关键逻辑与工作流

### 插件动态拼装流程
1.  **自动注册**: `nfcscript` 导入时会自动加载 `builtins.py`，完成 `crft` 核心组件的隐式注册。
2.  **实例化**: 调用 `init_nfc` 指定 Hardware/Driver 名称，引擎自动拼装。
3.  **绑定**: `bind_card()` 或 `find_card()` 实例化 Card 类。
4.  **DSL 执行**: 在模块层面直接调用卡片方法（`get_version()` 等）。

### find_card 双模式逻辑
```python
def find_card(self):
    card_info = self.find_raw()    # 物理寻卡，失败时抛出 RuntimeError
    uid = card_info["uid"]

    if self.active_tag is not None and hasattr(self, "_bind_card_name"):
        # 已有 bind → 复用其卡类型，忽略 SAK
        card_name = self._bind_card_name
    else:
        # 没有 bind → 从 SAK 自动猜测
        sak = card_info.get("sak")
        card_name = get_name_by_sak(sak)
        if not card_name:
            raise RuntimeError(f"未找到 SAK=0x{sak:02X} 对应的卡片驱动")

    card_class = get("card", card_name)
    self.active_tag = card_class(reader=self._driver, uid=uid)
    return self.active_tag
```

### DSL 函数转发流程（以 get_version 为例）
```
模块加载时:
  _make_wrapper("get_version") → _fn 函数

运行时:
  get_version()
    → _fn()
    → getattr(_get_controller(), "get_version")
    → NfcReader.__getattr__("get_version")
    → active_tag.get_version  (bound method)
    → ()  调用
```

### DSL 属性转发流程（以 driver/active_tag 为例）
```
模块加载时:
  _make_wrapper("driver") → _fn 函数

运行时:
  driver()
    → _fn()
    → getattr(_get_controller(), "driver")
    → NfcReader.driver (property getter)
    → <driver 对象>  (非 callable)
    → 直接返回 <driver 对象>
```

### init_nfc 诊断输出
每次 `init_nfc()` 自动打印:
- 已注册的 Hardware / Driver / Card 插件
- SAK 映射表
- NfcReader 的公开成员（`dir` 自动发现）
- init 完成后 `active_tag` 状态、类型和可用方法

## 5. 开发规范 (开发者请遵守)

*   **新增驱动/卡片**: 必须在 `builtins.py` 中通过 `register` 注册，或在运行脚本前手动注册。
*   **严禁硬编码**: 核心逻辑不允许显式 `import` 任何 `crft` 驱动的具体类，必须通过 `registry.get` 动态加载。
*   **`.pyi` 同步**: 在 `__init__.pyi` 和 `reader.pyi` 中声明新增的公开函数/方法签名。
*   **依赖注入**: 在初始化 `Driver` 或 `Card` 时，确保 Transport 和 Driver 对象作为参数传入。
*   **`register` 签名**: `register(category, name, klass, sak=None)` — 卡片注册时通过 `sak` 参数提供 SAK 映射。

## 6. 调试指南
*   若遇到 `AttributeError`，检查 `active_tag` 是否已通过 `bind_card` 或 `find_card` 正确绑定。
*   若遇到 `RuntimeError: NFC 控制器未初始化`，请确保已调用 `init_nfc()`。
*   若遇到 `RuntimeError: 物理层寻卡失败`，检查硬件连接和卡片是否在场。
*   若遇到 `ValueError: Plugin 'xxx' not found`，请核实是否在运行脚本前执行了 `register` 操作。
*   所有通信原始日志均由底层的 `crft.trace` 模块处理，若需调试物理链路，请配置 Trace Manager。
*   `_dump_init_info` 在每次 `init_nfc` 输出诊断信息，可快速确认插件注册和 API 暴露情况。

## 7. Development Policies (MUST FOLLOW)
*   **Architecture Synchronization**: 任何对项目架构、核心 API 或插件化机制的更新，都必须同步更新此 `AGENTS.md`。此文档是项目的"唯一事实来源"。
*   **Tooling Consistency**: 所有工作流操作（脚本运行、环境管理、依赖验证）必须且仅使用 `uv` 工具链。
*   **`.pyi` Syncing**: 修改 `NfcReader` 的公开接口或 `__init__.py` 的 `_make_wrapper` 导出的函数时，必须同步更新 `__init__.pyi` 和 `reader.pyi`。

---
*保持架构的简单与插件的独立性是本项目成功的关键。新增功能前请优先考虑通过注册中心实现，而非修改核心逻辑。*
