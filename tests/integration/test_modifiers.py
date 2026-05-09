import subprocess
import sys
import os

def test_modifier_edges():
    target = "tests/fixtures/Modifiers.sol"
    cmd = [sys.executable, "-m", "sol_callgraph.launcher", target, "--contract", "Derived", "--depth", "1"]
    result = subprocess.run(cmd, capture_output=True, text=True)
    
    assert result.returncode == 0
    # check edge from function to modifier
    assert '"Derived.declaredFunc()" -> "Derived.onlyAdmin()" [label="modifier"];' in result.stdout
    # check edge from modifier to checkAdmin
    assert '"Derived.onlyAdmin()" -> "Derived.checkAdmin()" [label="internal"];' in result.stdout
    # check edge from function to baseFunc (expandable/inherited)
    assert '"Derived.declaredFunc()" -> "Base.baseFunc()" [label="internal"];' in result.stdout

def test_root_scope_inheritance():
    # Base.baseFunc should NOT be a root function when targeting Derived
    target = "tests/fixtures/Modifiers.sol"
    cmd = [sys.executable, "-m", "sol_callgraph.launcher", target, "--contract", "Derived", "--depth", "1"]
    result = subprocess.run(cmd, capture_output=True, text=True)
    
    assert result.returncode == 0
    # Base.baseFunc should be expandable (dashed), not root (solid)
    assert '"Base.baseFunc()" [style="rounded,dashed"' in result.stdout
    assert '"Derived.declaredFunc()" [style="rounded"' in result.stdout
