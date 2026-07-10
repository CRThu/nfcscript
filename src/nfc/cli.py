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
    parser.add_argument("--trace-layer", default=None, help="启用的层 (逗号分隔: driver,debug,protocol,warning,error,app,all)")
    parser.add_argument("--trace-level", default=None, help="最低日志级别 (driver/debug/protocol/warning/error/app, 默认: warning)")

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

    # 解析 --trace-layer: 启用指定层 (调试用，默认已开启 protocol/warning/error/app)
    trace_env = os.environ.get("NFC_TRACE_LAYER", "")
    trace_arg = args.trace_layer or trace_env
    if trace_arg:
        trace.filter.level = "driver"  # 允许所有层可见
        for name in trace_arg.split(","):
            name = name.strip().lower()
            if name == "all":
                for layer in ["driver", "debug", "protocol", "warning", "error", "app"]:
                    setattr(trace.filter, layer, True)
            elif name:
                setattr(trace.filter, name, True)

    # 解析 --trace-level: 最低级别过滤
    level_env = os.environ.get("NFC_TRACE_LEVEL", "warning")
    level_arg = args.trace_level or level_env
    trace.filter.level = level_arg

    run_script(args.script)

if __name__ == "__main__":
    main()
