import subprocess
import sys
import os

def test_root_detection_foundry():
    target = "tests/fixtures/foundry_project/contracts/Vault.sol"
    cmd = [sys.executable, "-m", "sol_callgraph.launcher", target, "--print-env"]
    result = subprocess.run(cmd, capture_output=True, text=True)
    
    assert result.returncode == 0
    assert "target: tests/fixtures/foundry_project/contracts/Vault.sol" in result.stdout
    assert "detected root:" in result.stdout
    assert "foundry_project" in result.stdout
    assert "root reason: strong marker: foundry.toml" in result.stdout
    assert "slither cwd:" in result.stdout
    assert "foundry_project" in result.stdout
    assert "slither target: contracts/Vault.sol" in result.stdout

def test_explicit_root():
    target = "tests/fixtures/foundry_project/contracts/Vault.sol"
    explicit_root = os.path.abspath("tests/fixtures")
    cmd = [sys.executable, "-m", "sol_callgraph.launcher", target, "--root", explicit_root, "--print-env"]
    result = subprocess.run(cmd, capture_output=True, text=True)
    
    assert result.returncode == 0
    assert f"detected root: {explicit_root}" in result.stdout
    assert "root reason: explicitly set by --root" in result.stdout
    assert f"slither cwd: {explicit_root}" in result.stdout
    # slither target should be relative to the explicit root
    assert "slither target: foundry_project/contracts/Vault.sol" in result.stdout

def test_no_root_detect():
    target = "tests/fixtures/foundry_project/contracts/Vault.sol"
    cmd = [sys.executable, "-m", "sol_callgraph.launcher", target, "--no-root-detect", "--print-env"]
    result = subprocess.run(cmd, capture_output=True, text=True)
    
    assert result.returncode == 0
    assert f"detected root: {os.getcwd()}" in result.stdout
    assert "root reason: disabled by --no-root-detect" in result.stdout
