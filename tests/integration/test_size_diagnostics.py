import subprocess
import sys
import os

def test_max_nodes_limit():
    target = "external/openzeppelin-contracts/contracts/token/ERC20/ERC20.sol"
    # Set a very low limit to trigger truncation
    cmd = [sys.executable, "-m", "sol_callgraph.launcher", target, "--max-nodes", "5"]
    result = subprocess.run(cmd, capture_output=True, text=True)
    
    assert result.returncode == 0
    assert "Reached max nodes limit (5). Graph truncated." in result.stderr

def test_fail_on_unresolved():
    # ERC20 has some high-level calls that might be unresolved if not careful, 
    # but let's use a simpler way if possible.
    # Actually, almost all real contracts have some unresolved calls (e.g. builtins if not handled).
    # Wait, builtins are NOT unresolved, they are 'solidity'.
    
    # Low level call is a good candidate for unresolved
    fixture = "tests/fixtures/LowLevel.sol"
    with open(fixture, "w") as f:
        f.write("""
contract LowLevel {
    function callMe(address target) public {
        target.call("");
    }
}
""")
    
    # Without --fail-on-unresolved
    cmd = [sys.executable, "-m", "sol_callgraph.launcher", fixture]
    result = subprocess.run(cmd, capture_output=True, text=True)
    assert result.returncode == 0
    
    # With --fail-on-unresolved
    cmd = [sys.executable, "-m", "sol_callgraph.launcher", fixture, "--fail-on-unresolved"]
    result = subprocess.run(cmd, capture_output=True, text=True)
    assert result.returncode == 1
    assert "error: unresolved calls found" in result.stderr
    
    os.remove(fixture)

def test_fail_on_warning():
    # Multiple declarations trigger a warning
    target = "tests/fixtures/Multi.sol"
    cmd = [sys.executable, "-m", "sol_callgraph.launcher", target, "--fail-on-warning"]
    result = subprocess.run(cmd, capture_output=True, text=True)
    
    assert result.returncode == 1
    assert "error: warnings found" in result.stderr
