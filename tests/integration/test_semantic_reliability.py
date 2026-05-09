import subprocess
import sys
import os
import pytest

OZ_PATH = "external/openzeppelin-contracts"

@pytest.mark.skipif(not os.path.exists(OZ_PATH), reason="OpenZeppelin contracts not found")
def test_inherited_tooltip_clarity():
    target = os.path.join(OZ_PATH, "contracts/proxy/transparent/TransparentUpgradeableProxy.sol")
    cmd = [sys.executable, "-m", "sol_callgraph.launcher", target, "--contract", "TransparentUpgradeableProxy", "--include-inherited"]
    result = subprocess.run(cmd, capture_output=True, text=True)
    
    assert result.returncode == 0
    # Proxy._delegate tooltip should have declared in and viewed as
    # Using a part of the tooltip string to be safe with escapes
    assert 'declared in: Proxy' in result.stdout
    assert 'viewed as: TransparentUpgradeableProxy' in result.stdout

@pytest.mark.skipif(not os.path.exists(OZ_PATH), reason="OpenZeppelin contracts not found")
def test_label_disambiguation():
    target = os.path.join(OZ_PATH, "contracts/proxy/transparent/TransparentUpgradeableProxy.sol")
    cmd = [sys.executable, "-m", "sol_callgraph.launcher", target, "--contract", "TransparentUpgradeableProxy", "--include-inherited"]
    result = subprocess.run(cmd, capture_output=True, text=True)
    
    assert result.returncode == 0
    # Should have disambiguated labels for constructors and fallbacks
    assert 'label="TransparentUpgradeableProxy.constructor(address,address,bytes)"' in result.stdout
    assert 'label="ERC1967Proxy.constructor(address,bytes)"' in result.stdout
    assert 'label="TransparentUpgradeableProxy._fallback()"' in result.stdout
    assert 'label="Proxy._fallback()"' in result.stdout

def test_override_edge_visuals():
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
    cmd = [sys.executable, "-m", "sol_callgraph.launcher", fixture, "--include-overrides"]
    result = subprocess.run(cmd, capture_output=True, text=True)
    
    assert result.returncode == 0
    # override edge should be dashed and have constraint=false
    assert 'label="override"' in result.stdout
    assert 'style="dashed"' in result.stdout
    assert 'constraint=false' in result.stdout
    assert 'class="edge-override semantic non-execution"' in result.stdout
    assert 'non-execution' in result.stdout # in tooltip
    
    os.remove(fixture)

@pytest.mark.skipif(not os.path.exists(OZ_PATH), reason="OpenZeppelin contracts not found")
def test_constructor_classes():
    target = os.path.join(OZ_PATH, "contracts/proxy/transparent/TransparentUpgradeableProxy.sol")
    cmd = [sys.executable, "-m", "sol_callgraph.launcher", target, "--contract", "TransparentUpgradeableProxy", "--include-inherited"]
    result = subprocess.run(cmd, capture_output=True, text=True)
    
    assert result.returncode == 0
    # TUP constructor
    assert 'class="root function constructor deployment-entrypoint public"' in result.stdout
    # ERC1967Proxy constructor (inherited)
    assert 'inherited-constructor' in result.stdout
    assert 'deployment-entrypoint' in result.stdout

@pytest.mark.skipif(not os.path.exists(OZ_PATH), reason="OpenZeppelin contracts not found")
def test_builtin_error_event_splitting():
    target = os.path.join(OZ_PATH, "contracts/proxy/transparent/TransparentUpgradeableProxy.sol")
    
    # 1. --no-builtins: abi.decode and revert(uint256,uint256) hidden, 
    # but revert ProxyDeniedAdminAccess remains
    cmd = [sys.executable, "-m", "sol_callgraph.launcher", target, "--no-builtins", "--include-inherited"]
    result = subprocess.run(cmd, capture_output=True, text=True)
    assert '"abi.decode()"' not in result.stdout
    assert '"revert(uint256,uint256)"' not in result.stdout
    assert '"revert ProxyDeniedAdminAccess()"' in result.stdout
    assert 'class="error-like function"' in result.stdout
    
    # 2. --no-errors: revert ProxyDeniedAdminAccess hidden
    cmd = [sys.executable, "-m", "sol_callgraph.launcher", target, "--no-errors"]
    result = subprocess.run(cmd, capture_output=True, text=True)
    assert '"revert ProxyDeniedAdminAccess()"' not in result.stdout
