import argparse
import importlib
import inspect
import os
import sys

from nfc import *
from nfctester.registry import CardRegistry


def _load_external_cards(paths):
    """加载外部卡片模块，触发 @CardRegistry.register() 注册"""
    for path in paths:
        path = os.path.abspath(path)
        if path.endswith(".py"):
            module_name = os.path.splitext(os.path.basename(path))[0]
            sys.path.insert(0, os.path.dirname(path))
        elif os.path.isdir(path):
            module_name = os.path.basename(path)
            sys.path.insert(0, os.path.dirname(path))
        else:
            continue

        try:
            importlib.import_module(module_name)
            print(f"已加载: {module_name}")
        except Exception as e:
            print(f"加载 {module_name} 失败: {e}")


def _discover_external_cards():
    """从 NFC_CARD_PATH 环境变量自动发现并加载外部卡片"""
    card_path = os.environ.get("NFC_CARD_PATH")
    if not card_path:
        return

    # 支持多个路径，用分号分隔 (Windows) 或冒号分隔 (Unix)
    separator = ";" if os.name == "nt" else ":"
    paths = [p.strip() for p in card_path.split(separator) if p.strip()]
    if paths:
        _load_external_cards(paths)


def _get_methods(card):
    """获取卡片实例的所有公开方法（排除私有方法和基类方法）"""
    methods = {}
    for name in dir(card):
        if name.startswith("_"):
            continue
        attr = getattr(card, name)
        if callable(attr):
            methods[name] = attr
    return methods


def _print_methods(methods):
    """打印可用方法列表"""
    print("\n可用命令:")
    for name, method in sorted(methods.items()):
        sig = inspect.signature(method)
        doc = (method.__doc__ or "").strip().split("\n")[0]
        print(f"  {name}{sig}  - {doc}")
    print()


def _parse_value(s):
    """解析输入值：支持十六进制、十进制、字符串"""
    s = s.strip()
    if s.startswith("0x"):
        return int(s, 16)
    if s.startswith("b'") or s.startswith('b"'):
        return eval(s)
    try:
        return int(s)
    except ValueError:
        return s


def _call_method(method, args_str):
    """调用方法，自动解析参数"""
    sig = inspect.signature(method)
    params = list(sig.parameters.keys())

    if not args_str:
        # 无参数调用
        return method()

    # 解析参数
    raw_args = args_str.split()
    parsed = []
    for i, raw in enumerate(raw_args):
        parsed.append(_parse_value(raw))

    # 跳过 self
    if params and params[0] == "self":
        params = params[1:]

    # 处理 bytes 参数：将多个连续值合并为 bytes
    final_args = []
    i = 0
    while i < len(parsed):
        if i < len(params):
            param = sig.parameters[params[i] if params[0] != "self" else params[i]]
            annotation = param.annotation
            if annotation is bytes or (isinstance(annotation, type) and issubclass(annotation, bytes)):
                # 收集剩余参数作为 bytes
                remaining = [x for x in parsed[i:] if isinstance(x, (int, bytes))]
                if remaining and all(isinstance(x, int) for x in remaining):
                    final_args.append(bytes(remaining))
                elif remaining:
                    final_args.append(b"".join(x if isinstance(x, bytes) else bytes([x]) for x in remaining))
                break
        final_args.append(parsed[i])
        i += 1

    return method(*final_args)


def main():
    parser = argparse.ArgumentParser(
        prog="nfc-cli",
        description="NFC 交互式命令行工具"
    )
    parser.add_argument("-c", "--card", default=None, help="卡片类型 (如: mifare_classic, ntag224, sm7)")
    parser.add_argument("-p", "--port", default=None, help="串口号")
    parser.add_argument("-r", "--reader", default=None, help="读卡器类型 (默认: pn532)")
    parser.add_argument("-i", "--import", dest="imports", nargs="*", default=[], help="导入外部卡片模块 (文件或目录路径)")
    parser.add_argument("--list-cards", action="store_true", help="列出所有可用的卡片类型")

    args = parser.parse_args()

    # 从环境变量自动发现外部卡片
    _discover_external_cards()

    # 手动指定的外部卡片
    if args.imports:
        _load_external_cards(args.imports)

    if args.list_cards:
        print("可用卡片类型:")
        for name in sorted(CardRegistry.list()):
            print(f"  {name}")
        return

    if not args.card:
        parser.error("需要指定卡片类型 (-c/--card) 或使用 --list-cards 查看可用类型")

    try:
        connect(port=args.port, reader_type=args.reader)
    except Exception as e:
        print(f"连接读卡器失败: {e}")
        sys.exit(1)

    try:
        card = CardRegistry.create(args.card, reader=get_reader())
        methods = _get_methods(card)

        print(f"已连接卡片: {args.card}")
        _print_methods(methods)

        while True:
            try:
                line = input("> ").strip()
                if not line:
                    continue
                if line in ("quit", "exit", "q"):
                    break
                if line == "help":
                    _print_methods(methods)
                    continue

                parts = line.split(maxsplit=1)
                cmd_name = parts[0]
                args_str = parts[1] if len(parts) > 1 else ""

                if cmd_name not in methods:
                    print(f"未知命令: {cmd_name}，输入 help 查看可用命令")
                    continue

                result = _call_method(methods[cmd_name], args_str)
                if result is not None:
                    if isinstance(result, bytes):
                        print(f"→ {FORMAT_HEX(result)}")
                    elif isinstance(result, bool):
                        print(f"→ {'OK' if result else 'FAIL'}")
                    else:
                        print(f"→ {result}")

            except EOFError:
                break
            except KeyboardInterrupt:
                print()
            except Exception as e:
                print(f"错误: {e}")

    finally:
        close()
        print("已断开连接")


if __name__ == "__main__":
    main()
