import subprocess
import sys
import os
import pytest

OZ_PATH = "external/openzeppelin-contracts"

@pytest.mark.skipif(not os.path.exists(OZ_PATH), reason="OpenZeppelin contracts not found")
def test_tup_smoke():
    target = os.path.join(OZ_PATH, "contracts/proxy/transparent/TransparentUpgradeableProxy.sol")
    cmd = [sys.executable, "-m", "sol_callgraph.launcher", target, "--contract", "TransparentUpgradeableProxy", "--depth", "1"]
    result = subprocess.run(cmd, capture_output=True, text=True)
    
    assert result.returncode == 0
    # Check for root functions (declared in target)
    assert '"contracts/proxy/transparent/TransparentUpgradeableProxy.sol::TransparentUpgradeableProxy::_dispatchUpgradeToAndCall()"' in result.stdout
    # Check for library call
    assert '"contracts/proxy/transparent/TransparentUpgradeableProxy.sol::TransparentUpgradeableProxy::_dispatchUpgradeToAndCall()" -> "contracts/proxy/ERC1967/ERC1967Utils.sol::ERC1967Utils::upgradeToAndCall(address,bytes)" [label="library", class="edge-library"' in result.stdout
    # Proxy._fallback should be inherited and thus expandable (dashed)
    assert '"contracts/proxy/Proxy.sol::Proxy::_fallback()" [style="rounded,dashed"' in result.stdout

@pytest.mark.skipif(not os.path.exists(OZ_PATH), reason="OpenZeppelin contracts not found")
def test_erc20_smoke():
    target = os.path.join(OZ_PATH, "contracts/token/ERC20/ERC20.sol")
    cmd = [sys.executable, "-m", "sol_callgraph.launcher", target, "--list-contracts"]
    result = subprocess.run(cmd, capture_output=True, text=True)
    
    assert result.returncode == 0
    assert "ERC20" in result.stdout
    assert "contract" in result.stdout
