import subprocess
import sys
import os

def test_entrypoint_metadata():
    target = "tests/fixtures/Modifiers.sol"
    cmd = [sys.executable, "-m", "sol_callgraph.launcher", target, "--contract", "Derived"]
    result = subprocess.run(cmd, capture_output=True, text=True)
    
    assert result.returncode == 0
    # declaredFunc is public, so it should be an entrypoint
    assert 'class="root function entrypoint public"' in result.stdout
    # onlyAdmin is a modifier
    assert 'class="root modifier"' in result.stdout

def test_include_overrides():
    fixture = "tests/fixtures/Overrides.sol"
    with open(fixture, "w") as f:
        f.write("""
contract Base {
    function foo() public virtual {}
}
contract Child is Base {
    function foo() public override {}
}
""")
    
    # Default: no overrides
    cmd = [sys.executable, "-m", "sol_callgraph.launcher", fixture, "--contract", "Child"]
    result = subprocess.run(cmd, capture_output=True, text=True)
    assert 'label="override"' not in result.stdout
    
    # With --include-overrides
    cmd = [sys.executable, "-m", "sol_callgraph.launcher", fixture, "--contract", "Child", "--include-overrides"]
    result = subprocess.run(cmd, capture_output=True, text=True)
    assert result.returncode == 0
    assert 'label="override"' in result.stdout
    # Match with stable IDs
    assert '"tests/fixtures/Overrides.sol::Child::foo()" -> "tests/fixtures/Overrides.sol::Base::foo()" [label="override"' in result.stdout
    
    os.remove(fixture)

def test_initializer_detection():
    fixture = "tests/fixtures/Initializers.sol"
    with open(fixture, "w") as f:
        f.write("""
contract Initializable {
    function initialize() public {}
    function __Ownable_init() internal {}
}
""")
    
    cmd = [sys.executable, "-m", "sol_callgraph.launcher", fixture]
    result = subprocess.run(cmd, capture_output=True, text=True)
    
    assert result.returncode == 0
    assert 'class="root function entrypoint public initializer"' in result.stdout
    assert 'class="root function internal initializer"' in result.stdout
    
    os.remove(fixture)
