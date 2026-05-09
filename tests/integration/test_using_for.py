import subprocess
import sys
import os

def test_using_for():
    target = "tests/fixtures/UsingFor.sol"
    cmd = [sys.executable, "-m", "sol_callgraph.launcher", target, "--contract", "UsingFor"]
    result = subprocess.run(cmd, capture_output=True, text=True)
    
    assert result.returncode == 0
    # Should show call from UsingFor.test to Lib.add
    assert '"Lib.add(uint256,uint256)"' in result.stdout
    assert 'label="library"' in result.stdout
