import subprocess
import sys
import os

def test_debug_slither():
    target = "tests/fixtures/Simple.sol"
    cmd = [sys.executable, "-m", "sol_callgraph.launcher", target, "--debug-slither", "--solc-args=--optimize"]
    result = subprocess.run(cmd, capture_output=True, text=True)
    
    assert result.returncode == 0
    assert "DEBUG: slither invocation" in result.stderr
    assert f"target: {target}" in result.stderr
    assert "solc_args: --optimize" in result.stderr
