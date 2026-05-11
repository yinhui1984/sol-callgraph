import os
import shutil
import sys
import subprocess
from typing import Optional, Tuple

FALLBACK_SLITHER_BINS = [
    "/opt/homebrew/bin/slither",
    "/usr/local/bin/slither",
    "~/.pyenv/shims/slither",
]

FALLBACK_PYTHON_BINS = [
    "/opt/homebrew/bin/python3",
    "/usr/local/bin/python3",
    "~/.pyenv/shims/python3",
]

def find_slither_bin() -> Optional[str]:
    """Finds the slither binary in PATH."""
    return shutil.which("slither")

def resolve_slither_executable(slither_path: str) -> str:
    """Resolves symlinks for the slither executable."""
    return os.path.realpath(slither_path)

def infer_python_from_shebang(executable_path: str) -> Optional[str]:
    """
    Reads the shebang of the executable and infers the Python interpreter.
    Supports:
    - #!/usr/bin/env python3
    - #!/absolute/path/to/python
    """
    try:
        with open(executable_path, 'rb') as f:
            line = f.readline().decode('utf-8', errors='ignore').strip()
            if not line.startswith('#!'):
                return None
            
            shebang = line[2:].strip()
            if 'env' in shebang:
                parts = shebang.split()
                # Find the part after 'env'
                for i, part in enumerate(parts):
                    if part.endswith('env') and i + 1 < len(parts):
                        python_cmd = parts[i+1]
                        if os.path.basename(python_cmd).startswith("python"):
                            return shutil.which(python_cmd)
                        return None
                return None
            else:
                if not os.path.basename(shebang).startswith("python"):
                    return None
                return shebang
    except Exception:
        return None

def _dedupe_paths(paths: list[str]) -> list[str]:
    seen = set()
    result = []
    for path in paths:
        expanded = os.path.expanduser(path)
        key = os.path.realpath(expanded)
        if key in seen:
            continue
        seen.add(key)
        result.append(expanded)
    return result

def find_slither_bins() -> list[str]:
    """Finds slither binaries in PATH, then common macOS fallback locations."""
    path = os.environ.get("PATH", "")
    bins = []
    for dir in path.split(os.pathsep):
        if not dir:
            continue
        bin_path = os.path.join(dir, "slither")
        if os.path.isfile(bin_path) and os.access(bin_path, os.X_OK):
            bins.append(bin_path)
    for bin_path in FALLBACK_SLITHER_BINS:
        expanded = os.path.expanduser(bin_path)
        if os.path.isfile(expanded) and os.access(expanded, os.X_OK):
            bins.append(expanded)
    return _dedupe_paths(bins)

def find_python_bins() -> list[str]:
    """Finds python3 in PATH, then common macOS fallback locations."""
    bins = []
    python3 = shutil.which("python3")
    if python3:
        bins.append(python3)
    for bin_path in FALLBACK_PYTHON_BINS:
        expanded = os.path.expanduser(bin_path)
        if os.path.isfile(expanded) and os.access(expanded, os.X_OK):
            bins.append(expanded)
    return _dedupe_paths(bins)

def validate_slither_python(python_path: str) -> bool:
    """Checks if the given python can import slither."""
    if not python_path or not os.path.isfile(python_path):
        return False
    try:
        # Try to import slither
        result = subprocess.run([python_path, "-c", "import slither"], capture_output=True, text=True)
        return result.returncode == 0
    except Exception:
        return False

def detect_slither_env() -> Tuple[Optional[str], Optional[str], Optional[str]]:
    """
    Detects the slither environment.
    Returns (slither_path, resolved_slither_path, slither_python_path).
    """
    slither_bins = find_slither_bins()
    
    for slither_path in slither_bins:
        resolved_path = resolve_slither_executable(slither_path)
        python_path = infer_python_from_shebang(resolved_path)
        
        if python_path and validate_slither_python(python_path):
            return slither_path, resolved_path, python_path
            
    # If we couldn't find one via shebang, try python3 candidates that can import slither.
    for python3 in find_python_bins():
        if validate_slither_python(python3):
            slither_path = find_slither_bin()
            return slither_path, slither_path, python3

    return None, None, None

def find_project_root(target_path: str) -> Tuple[str, str]:
    """
    Detects the project root by looking for markers.
    Returns (root_path, reason).
    """
    strong_markers = [
        "foundry.toml", "hardhat.config.ts", "hardhat.config.js",
        "hardhat.config.cjs", "hardhat.config.mjs", "truffle-config.js",
        "truffle.js", "brownie-config.yaml", "ape-config.yaml", "dapp.json"
    ]
    weak_markers = ["remappings.txt", "package.json", ".git"]
    
    abs_target = os.path.abspath(target_path)
    current_dir = os.path.dirname(abs_target) if os.path.isfile(abs_target) else abs_target
    
    # Search for strong markers first
    search_dir = current_dir
    while True:
        for marker in strong_markers:
            if os.path.exists(os.path.join(search_dir, marker)):
                return search_dir, f"strong marker: {marker}"
        
        parent = os.path.dirname(search_dir)
        if parent == search_dir:
            break
        search_dir = parent
        
    # Search for weak markers
    search_dir = current_dir
    while True:
        for marker in weak_markers:
            if os.path.exists(os.path.join(search_dir, marker)):
                return search_dir, f"weak marker: {marker}"
        
        parent = os.path.dirname(search_dir)
        if parent == search_dir:
            break
        search_dir = parent
        
    return current_dir, "no markers found, using target directory"

def debug_env():
    """Outputs the detected slither environment to stdout. (Phase 1 legacy)"""
    slither_path, resolved_path, python_path = detect_slither_env()
    
    if not slither_path:
        print("error: slither not found in PATH", file=sys.stderr)
        sys.exit(2)
    
    print(f"slither: {slither_path}")
    print(f"resolved slither: {resolved_path}")
    print(f"slither python: {python_path or 'unknown'}")
    
    if not python_path:
        print("error: could not infer python from slither shebang", file=sys.stderr)
        sys.exit(2)

def print_env_info(target: Optional[str], root: Optional[str], reason: str, slither_cwd: str, 
                   slither_target: str, slither_bin: Optional[str], slither_python: Optional[str]):
    """Prints environment information as requested in Phase 2."""
    print(f"target: {target or 'N/A'}")
    print(f"detected root: {root or 'N/A'}")
    print(f"root reason: {reason}")
    print(f"slither cwd: {slither_cwd}")
    print(f"slither target: {slither_target}")
    print(f"slither binary: {slither_bin or 'N/A'}")
    print(f"slither python: {slither_python or 'N/A'}")
