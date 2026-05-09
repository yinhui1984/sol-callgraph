import sys
import subprocess
import os
from sol_callgraph.slither_env import detect_slither_env, debug_env, find_project_root, print_env_info

def main():
    # Minimal argument parsing for launcher
    args = sys.argv[1:]
    
    if "--debug-env" in args:
        debug_env()
        sys.exit(0)
    
    # Handle launcher-only and shared args
    slither_python = None
    root_dir = None
    no_root_detect = "--no-root-detect" in args
    is_print_env = "--print-env" in args
    target = None
    
    # Simple arg parsing for launcher needs
    new_args = []
    skip_next = False
    for i, arg in enumerate(args):
        if skip_next:
            skip_next = False
            continue
        if arg == "--slither-python" and i + 1 < len(args):
            slither_python = args[i+1]
            skip_next = True
        elif arg.startswith("--slither-python="):
            slither_python = arg.split("=", 1)[1]
        elif arg == "--root" and i + 1 < len(args):
            root_dir = args[i+1]
            skip_next = True
            new_args.append(arg)
            new_args.append(args[i+1])
        elif arg.startswith("--root="):
            root_dir = arg.split("=", 1)[1]
            new_args.append(arg)
        elif not arg.startswith("-"):
            if target is None:
                target = arg
            new_args.append(arg)
        else:
            new_args.append(arg)

    if not slither_python:
        _, _, slither_python = detect_slither_env()
    
    slither_path, _, _ = detect_slither_env()

    # Root detection
    detected_root = None
    root_reason = "disabled by --no-root-detect"
    if no_root_detect:
        detected_root = os.getcwd()
    elif root_dir:
        detected_root = os.path.abspath(root_dir)
        root_reason = "explicitly set by --root"
    elif target:
        detected_root, root_reason = find_project_root(target)
    else:
        detected_root = os.getcwd()
        root_reason = "no target specified, using cwd"

    # Prepare Slither CWD and target
    slither_cwd = detected_root
    slither_target = target
    if target and os.path.isabs(target):
        if target.startswith(detected_root):
            slither_target = os.path.relpath(target, detected_root)
    elif target:
        abs_target = os.path.abspath(target)
        if abs_target.startswith(detected_root):
            slither_target = os.path.relpath(abs_target, detected_root)
        else:
            slither_target = abs_target

    if is_print_env:
        print_env_info(target, detected_root, root_reason, slither_cwd, 
                       slither_target, slither_path, slither_python)
        sys.exit(0)

    if not slither_python:
        print("error: could not find slither python. Use --slither-python to specify it.", file=sys.stderr)
        sys.exit(2)

    # Core is located in the same package
    package_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    env = os.environ.copy()
    if "PYTHONPATH" in env:
        env["PYTHONPATH"] = f"{package_root}:{env['PYTHONPATH']}"
    else:
        env["PYTHONPATH"] = package_root

    # Update args for core: replace original target with slither_target if needed
    # This is slightly tricky because we don't know where target was in the list
    # But we can just use new_args which we built.
    
    # For now, let's just use the original args but with the correctly set cwd.
    # If Slither needs the relative path to resolve imports, slither_target is better.
    
    final_args = []
    for arg in new_args:
        if arg == target:
            final_args.append(slither_target)
        else:
            final_args.append(arg)

    cmd = [slither_python, "-m", "sol_callgraph.core"] + final_args
    try:
        result = subprocess.run(cmd, env=env, cwd=slither_cwd)
        sys.exit(result.returncode)
    except FileNotFoundError:
        print(f"error: python interpreter not found: {slither_python}", file=sys.stderr)
        sys.exit(2)
    except Exception as e:
        print(f"error: failed to execute core: {e}", file=sys.stderr)
        sys.exit(2)

if __name__ == "__main__":
    main()
