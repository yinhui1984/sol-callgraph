import subprocess
import sys
import os

def test_include_inherited():
    target = "tests/fixtures/Modifiers.sol"
    # Without include-inherited
    cmd = [sys.executable, "-m", "sol_callgraph.launcher", target, "--contract", "Derived"]
    result = subprocess.run(cmd, capture_output=True, text=True)
    assert '"tests/fixtures/Modifiers.sol::Base::baseFunc()" [style="rounded,dashed"' in result.stdout # expandable

    # With include-inherited
    cmd = [sys.executable, "-m", "sol_callgraph.launcher", target, "--contract", "Derived", "--include-inherited"]
    result = subprocess.run(cmd, capture_output=True, text=True)
    assert result.returncode == 0
    # Base.baseFunc should now be root (solid) and have 'inherited' class
    assert '"tests/fixtures/Modifiers.sol::Base::baseFunc()" [style="rounded"' in result.stdout
    assert 'class="root function public-entrypoint public inherited"' in result.stdout

def test_root_function_specific():
    target = "tests/fixtures/Modifiers.sol"
    cmd = [sys.executable, "-m", "sol_callgraph.launcher", target, "--root-function", "Derived.declaredFunc()"]
    result = subprocess.run(cmd, capture_output=True, text=True)
    assert result.returncode == 0
    assert '"tests/fixtures/Modifiers.sol::Derived::declaredFunc()"' in result.stdout
    assert '"tests/fixtures/Modifiers.sol::Derived::checkAdmin()"' not in result.stdout # should be expandable, but depth 1 might not show it as root

def test_root_function_ambiguous():
    # Create a fixture with overloads
    fixture = "tests/fixtures/Overloads.sol"
    with open(fixture, "w") as f:
        f.write("""
contract Overloads {
    function foo(uint256) public {}
    function foo(address) public {}
}
""")
    
    cmd = [sys.executable, "-m", "sol_callgraph.launcher", fixture, "--root-function", "foo"]
    result = subprocess.run(cmd, capture_output=True, text=True)
    
    assert result.returncode == 3
    assert "error: function name `foo` is ambiguous" in result.stderr
    assert "Overloads.foo(uint256)" in result.stderr
    assert "Overloads.foo(address)" in result.stderr
    
    os.remove(fixture)

def test_include_interfaces():
    target = "tests/fixtures/Multi.sol"
    # Without include-interfaces
    cmd = [sys.executable, "-m", "sol_callgraph.launcher", target]
    result = subprocess.run(cmd, capture_output=True, text=True)
    assert '"tests/fixtures/Multi.sol::I::i()"' not in result.stdout
    
    # With include-interfaces
    cmd = [sys.executable, "-m", "sol_callgraph.launcher", target, "--include-interfaces"]
    result = subprocess.run(cmd, capture_output=True, text=True)
    assert result.returncode == 0
    assert '"tests/fixtures/Multi.sol::I::i()"' in result.stdout
