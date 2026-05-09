import os
import subprocess
import sys

def test_basic_dot_output():
    target = "tests/fixtures/Simple.sol"
    # Run via launcher to test the whole flow
    cmd = [sys.executable, "-m", "sol_callgraph.launcher", target]
    result = subprocess.run(cmd, capture_output=True, text=True)
    
    assert result.returncode == 0
    assert "digraph focused_call_graph {" in result.stdout
    assert '"tests/fixtures/Simple.sol::Simple::foo()"' in result.stdout
    assert '"tests/fixtures/Simple.sol::Simple::bar()"' in result.stdout
    assert '"tests/fixtures/Simple.sol::Simple::foo()" -> "tests/fixtures/Simple.sol::Simple::bar()" [label="internal", class="edge-internal"' in result.stdout

def test_list_contracts():
    target = "tests/fixtures/Simple.sol"
    cmd = [sys.executable, "-m", "sol_callgraph.launcher", target, "--list-contracts"]
    result = subprocess.run(cmd, capture_output=True, text=True)
    
    assert result.returncode == 0
    assert "Simple" in result.stdout
    assert "contract" in result.stdout
