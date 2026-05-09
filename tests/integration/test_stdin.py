import subprocess
import sys
import os

def test_reject_stdin():
    cmd = [sys.executable, "-m", "sol_callgraph.launcher", "-"]
    result = subprocess.run(cmd, capture_output=True, text=True, env={**os.environ, "LANG": "en_US.UTF-8"})
    
    assert result.returncode == 1
    assert "error: stdin input '-' is not supported" in result.stderr
