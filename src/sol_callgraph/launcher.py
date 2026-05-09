import sys
import subprocess
import os
from sol_callgraph.slither_env import detect_slither_env, debug_env

def main():
    # Minimal argument parsing for launcher
    args = sys.argv[1:]
    
    slither_python = None
    if "--debug-env" in args:
        debug_env()
        sys.exit(0)
    
    # Check for --slither-python
    for i, arg in enumerate(args):
        if arg == "--slither-python" and i + 1 < len(args):
            slither_python = args[i+1]
            # Remove --slither-python and its value from args for core
            args = args[:i] + args[i+2:]
            break
        elif arg.startswith("--slither-python="):
            slither_python = arg.split("=", 1)[1]
            args = args[:i] + args[i+1:]
            break

    if not slither_python:
        _, _, slither_python = detect_slither_env()
    
    if not slither_python:
        print("error: could not find slither python. Use --slither-python to specify it.", file=sys.stderr)
        sys.exit(2)

    # Core is located in the same package
    # We need to run it with the slither_python
    # We'll use -m sol_callgraph.core
    
    # We need to make sure src is in PYTHONPATH for the subprocess
    # Since we are installed in editable mode, it should be fine if we are in the environment.
    # But to be safe, we can add the current package path to PYTHONPATH.
    
    package_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    env = os.environ.copy()
    if "PYTHONPATH" in env:
        env["PYTHONPATH"] = f"{package_root}:{env['PYTHONPATH']}"
    else:
        env["PYTHONPATH"] = package_root

    cmd = [slither_python, "-m", "sol_callgraph.core"] + args
    try:
        result = subprocess.run(cmd, env=env)
        sys.exit(result.returncode)
    except FileNotFoundError:
        print(f"error: python interpreter not found: {slither_python}", file=sys.stderr)
        sys.exit(2)
    except Exception as e:
        print(f"error: failed to execute core: {e}", file=sys.stderr)
        sys.exit(2)

if __name__ == "__main__":
    main()
