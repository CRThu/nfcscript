import sys
import argparse
import os
import runpy

from dotenv import load_dotenv

def run_script(script_path):
    script_dir = os.path.dirname(os.path.abspath(script_path))
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
    parser.add_argument("--trace-level", default="INFO", help="日志级别 (默认: INFO)")

    args = parser.parse_args()

    if not os.path.exists(args.script):
        print(f"Error: Script not found: {args.script}")
        sys.exit(1)

    script_dir = os.path.dirname(os.path.abspath(args.script))
    script_env = os.path.join(script_dir, ".env")
    if os.path.exists(script_env):
        load_dotenv(script_env, override=False)
    load_dotenv(override=False)

    if args.port is not None:
        os.environ["NFC_PORT"] = args.port
    if args.reader is not None:
        os.environ["NFC_READER"] = args.reader

    from nfc import trace
    if args.trace_driver:
        trace.set_layer("DRIVER", True)
    if args.trace_protocol:
        trace.set_layer("PROTOCOL", True)
    trace.set_level(args.trace_level)

    run_script(args.script)

if __name__ == "__main__":
    main()
