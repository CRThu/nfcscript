# AGENTS.md: nfcscript 项目架构说明书 (AI 专用)

## 1. 项目概述
`nfcscript` 是一个轻量级、完全插件化的 NFC 测试核心引擎。它不依赖于任何具体的硬件驱动，而是作为**插件加载器 (Plugin Loader)** 和 **DSL 执行环境**，将底层的 `CarrotRFIDTester` (crft) 逻辑封装为简洁的自动化测试接口。

## 2. 架构设计：三层动态插件模式
本项目遵循“解耦”原则，硬件、驱动与卡片逻辑均支持动态注册与加载，实现零硬编码耦合。

*   **Hardware Layer (传输层)**: 负责物理通信 (如 `SerialTransport`)。
*   **Driver Layer (协议层)**: 负责硬件读写指令处理 (如 `PN532_HSU`)。
*   **Card Layer (业务层)**: 负责卡片内部指令集与逻辑 (如 `NTAG21x`)。

## 3. 核心组件 (src/nfcscript/)

### `registry.py`: 注册中心
所有插件必须通过 `register(category, name, klass, **kwargs)` 进行注册。
*   **Categories**: `hardware`, `driver`, `card`。
*   **特性**: 支持通过 `sak` (Select Acknowledge) 自动映射卡片驱动。

### `wrapper.py`: NfcController (外观模式)
这是引擎的核心 Orchestrator。
*   **职责**: 动态拼装传输层和驱动层，持有当前的 `active_tag` 对象。
*   **动态代理 (`__getattr__`)**: 实现了 Python 动态代理，将对 `NfcController` 的方法调用（如 `get_version()`）自动转发给当前绑定的 `active_tag`，实现 DSL 的平滑接口调用。
*   **双模式绑定**:
    *   `bind_card(name, uid)`: 手动指定卡类型，跳过寻卡。
    *   `find_card()`: 调用物理寻卡，自动探测并匹配驱动。

### `__init__.py`: DSL 入口
提供全局单例访问与接口平展：
*   `get_nfc()`: 工厂方法，通过配置名称动态拼装控制器实例。
*   `ASSERT`: 暴露测试断言工具。

## 4. 关键逻辑与工作流

### 插件动态拼装流程
1.  **注册**: 通过 `register` 将具体的类添加到全局 `_REGISTRY` 中。
2.  **实例化**: 调用 `get_nfc` 指定 Hardware/Driver 名称，引擎自动拼装。
3.  **绑定**: 调用 `find_card()` 或 `bind_card()` 实例化 Card 类。
4.  **DSL 执行**: 直接在 Controller 上调用卡片方法。

### 自动寻卡匹配逻辑
```python
# find_card 内部流向
1. self._driver.find() -> 获取 card_info (含 SAK)
2. get_name_by_sak(sak) -> 匹配 card_name
3. get("card", card_name) -> 获取驱动类
4. self.active_tag = CardClass(...)
```

## 5. 开发规范 (开发者请遵守)

*   **新增驱动/卡片**: 必须在 `examples` 或 `main` 启动逻辑中通过 `register` 进行注册。
*   **严禁硬编码**: 核心逻辑 `wrapper.py` 不允许显式 `import` 任何 `crft` 驱动的具体类，必须通过 `registry.get` 进行动态加载。
*   **DSL 风格**: 新增的功能应当尽可能封装为 `NfcController` 的方法，以便通过 `__getattr__` 转发。
*   **依赖注入**: 在初始化 `Driver` 或 `Card` 时，确保 Transport 和 Driver 对象作为参数传入。

## 6. 调试指南
*   若遇到 `AttributeError`，检查 `active_tag` 是否已通过 `bind_card` 或 `find_card` 正确绑定。
*   若遇到 `ValueError: Plugin 'xxx' not found`，请核实是否在运行脚本前执行了 `register` 操作。
*   所有通信原始日志均由底层的 `crft.trace` 模块处理，若需调试物理链路，请配置 Trace Manager。

## 7. Development Policies (MUST FOLLOW)
*   **Architecture Synchronization**: 任何对项目架构、核心 API 或插件化机制的更新，都必须同步更新此 `AGENTS.md`。此文档是项目的“唯一事实来源”。
*   **Tooling Consistency**: 所有工作流操作（脚本运行、环境管理、依赖验证）必须且仅使用 `uv` 工具链。

---
*保持架构的简单与插件的独立性是本项目成功的关键。新增功能前请优先考虑通过注册中心实现，而非修改 `wrapper.py` 内部逻辑。*
