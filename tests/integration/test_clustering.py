import subprocess
import sys
import os

def test_cluster_output():
    target = "tests/fixtures/Multi.sol"
    # Default: no cluster
    cmd = [sys.executable, "-m", "sol_callgraph.launcher", target]
    result = subprocess.run(cmd, capture_output=True, text=True)
    assert "subgraph" not in result.stdout
    
    # With --cluster
    cmd = [sys.executable, "-m", "sol_callgraph.launcher", target, "--cluster"]
    result = subprocess.run(cmd, capture_output=True, text=True)
    assert result.returncode == 0
    assert "subgraph" in result.stdout
    # Should have cluster for Contract C and Library L
    assert 'label="C"' in result.stdout
    assert 'label="L"' in result.stdout
    assert 'cluster_C' in result.stdout
    assert 'cluster_L' in result.stdout
