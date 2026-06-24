import sys
import argparse
import os
import runpy

from dotenv import load_dotenv

def _find_dotenv_all(start_dir):
    chain = []
    path = start_dir
    while True:
        env_path = os.path.join(path, ".env")
        if os.path.exists(env_path):
            chain.append(env_path)
        parent = os.path.dirname(path)
        if parent == path:
            break
        path = parent
    chain.reverse()
    return chain

def _parse_level(value: str) -> int:
    """将字符串解析为解析级别，支持数字和别名"""
    val = value.lower().strip()
    if val in ("0", "false", "no", "off"):
        return 0
    if val in ("1", "simple", "summary"):
        return 1
    if val in ("2", "full", "tree"):
        return 2
    try:
        return int(value)
    except ValueError:
        return 1

def run_script(script_path):
    script_dir = os.path.dirname(os.path.abspath(script_path))
    cwd = os.getcwd()

    # 1. 加入当前工作目录 (CWD)，优先级最高
    if cwd not in sys.path:
        sys.path.insert(0, cwd)
        
    # 2. 加入脚本所在目录 (如果不是 CWD 的话)
    if script_dir != cwd and script_dir not in sys.path:
        sys.path.insert(0, script_dir)

    runpy.run_path(script_path, run_name="__main__")

def main():
    parser = argparse.ArgumentParser(
        prog="nfcscript",
        description="NFC Script Runner - 执行 NFC 测试脚本"
    )
    parser.add_argument("script", help="脚本文件路径")
    parser.add_argument("-p", "--port", default=None, help="串口号 (默认: NFC_PORT 环境变量或 COM20)")
    parser.add_argument("-r", "--reader", default=None, help="读卡器类型 (默认: NFC_READER 环境变量或 pn532)")
    parser.add_argument("--trace-driver", action="store_true", help="开启 DRIVER 层追踪")
    parser.add_argument("--trace-protocol", action="store_true", help="开启 PROTOCOL 层追踪")
    parser.add_argument("--trace-parse", type=int, default=None, choices=[0, 1, 2],
                        help="解析级别: 0=关闭 1=简单 2=复杂 (默认: NFC_TRACE_PARSE 或 1)")
    parser.add_argument("--trace-card-type", default=None,
                        help="卡片类型标识 (默认: NFC_TRACE_CARD_TYPE)")
    parser.add_argument("--trace-level", default="INFO", help="日志级别 (默认: INFO)")

    args, extra = parser.parse_known_args()

    if not os.path.exists(args.script):
        print(f"Error: Script not found: {args.script}")
        sys.exit(1)

    sys.argv = [args.script] + extra

    script_dir = os.path.dirname(os.path.abspath(args.script))
    dotenv_files = _find_dotenv_all(script_dir)
    for dotenv_path in dotenv_files:
        load_dotenv(dotenv_path, override=True)

    if args.port is not None:
        os.environ["NFC_PORT"] = args.port
    if args.reader is not None:
        os.environ["NFC_READER"] = args.reader

    from nfc import trace

    trace_level = os.environ.get("NFC_TRACE_LEVEL", "INFO")
    trace_driver = os.environ.get("NFC_TRACE_DRIVER", "").lower() in ("1", "true", "yes")
    trace_protocol = os.environ.get("NFC_TRACE_PROTOCOL", "").lower() in ("1", "true", "yes")
    trace_parse = os.environ.get("NFC_TRACE_PARSE", "1")
    trace_card_type = os.environ.get("NFC_TRACE_CARD_TYPE")
    trace_width = os.environ.get("NFC_TRACE_WIDTH")

    if args.trace_level != "INFO":
        trace_level = args.trace_level
    if args.trace_driver:
        trace_driver = True
    if args.trace_protocol:
        trace_protocol = True
    if args.trace_parse is not None:
        trace_parse = str(args.trace_parse)
    if args.trace_card_type is not None:
        trace_card_type = args.trace_card_type

    trace.set_level(trace_level)
    trace.set_layer("DRIVER", trace_driver)
    trace.set_layer("PROTOCOL", trace_protocol)
    trace.set_parse(_parse_level(trace_parse))
    if trace_card_type is not None:
        trace.set_card_type(trace_card_type)
    if trace_width is not None:
        os.environ["CRFT_TRACE_WIDTH"] = trace_width

    run_script(args.script)

if __name__ == "__main__":
    main()
