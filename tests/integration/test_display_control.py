import subprocess
import sys
import os

def test_no_constructors():
    target = "external/openzeppelin-contracts/contracts/token/ERC20/ERC20.sol"
    
    # Default: includes constructor
    cmd = [sys.executable, "-m", "sol_callgraph.launcher", target, "--contract", "ERC20", "--depth", "1"]
    result = subprocess.run(cmd, capture_output=True, text=True)
    assert '"contracts/token/ERC20/ERC20.sol::ERC20::constructor(string,string)"' in result.stdout
    
    # With --no-constructors
    cmd = [sys.executable, "-m", "sol_callgraph.launcher", target, "--contract", "ERC20", "--no-constructors", "--depth", "1"]
    result = subprocess.run(cmd, capture_output=True, text=True)
    assert '"contracts/token/ERC20/ERC20.sol::ERC20::constructor(string,string)"' not in result.stdout

def test_include_events():
    target = "external/openzeppelin-contracts/contracts/token/ERC20/ERC20.sol"
    # Default: no events
    cmd = [sys.executable, "-m", "sol_callgraph.launcher", target, "--contract", "ERC20", "--depth", "1"]
    result = subprocess.run(cmd, capture_output=True, text=True)
    assert 'label="event"' not in result.stdout
    
    # With --include-events
    # We need to target a function that emits an event, e.g., _update
    cmd = [sys.executable, "-m", "sol_callgraph.launcher", target, "--root-function", "ERC20._update", "--include-events"]
    result = subprocess.run(cmd, capture_output=True, text=True)
    assert result.returncode == 0
    assert 'label="event"' in result.stdout
    assert '"emit Transfer"' in result.stdout

def test_no_errors():
    target = "external/openzeppelin-contracts/contracts/token/ERC20/ERC20.sol"
    # Default: includes reverts
    cmd = [sys.executable, "-m", "sol_callgraph.launcher", target, "--root-function", "ERC20._update"]
    result = subprocess.run(cmd, capture_output=True, text=True)
    assert '"revert ERC20InsufficientBalance(address,uint256,uint256)"' in result.stdout
    
    # With --no-errors
    cmd = [sys.executable, "-m", "sol_callgraph.launcher", target, "--root-function", "ERC20._update", "--no-errors"]
    result = subprocess.run(cmd, capture_output=True, text=True)
    assert '"revert ERC20InsufficientBalance(address,uint256,uint256)"' not in result.stdout

def test_no_builtins():
    target = "external/openzeppelin-contracts/contracts/proxy/transparent/TransparentUpgradeableProxy.sol"
    # Default: includes abi.decode
    cmd = [sys.executable, "-m", "sol_callgraph.launcher", target, "--contract", "TransparentUpgradeableProxy"]
    result = subprocess.run(cmd, capture_output=True, text=True)
    assert '"abi.decode()"' in result.stdout
    
    # With --no-builtins
    cmd = [sys.executable, "-m", "sol_callgraph.launcher", target, "--contract", "TransparentUpgradeableProxy", "--no-builtins"]
    result = subprocess.run(cmd, capture_output=True, text=True)
    assert '"abi.decode()"' not in result.stdout
