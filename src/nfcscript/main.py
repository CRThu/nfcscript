import sys
import argparse
import os
import runpy

def run_script(script_path):
    # Add the script's directory to sys.path so it can find its dependencies
    script_dir = os.path.dirname(os.path.abspath(script_path))
    sys.path.insert(0, script_dir)
    
    # Run the script as a module
    runpy.run_path(script_path)

def main():
    print("Hello from nfcscript!")
    parser = argparse.ArgumentParser(description="NFC Script Runner")
    parser.add_argument("script", help="Path to the script to run")
    args = parser.parse_args()
    
    if not os.path.exists(args.script):
        print(f"Error: Script not found: {args.script}")
        sys.exit(1)
        
    run_script(args.script)

if __name__ == "__main__":
    main()
