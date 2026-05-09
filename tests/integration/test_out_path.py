import subprocess
import sys
import os
import pytest
import json

OZ_PATH = "external/openzeppelin-contracts"

@pytest.mark.skipif(not os.path.exists(OZ_PATH), reason="OpenZeppelin contracts not found")
def test_relative_out_path_resolution():
    # Target a file in OZ root (will cause chdir)
    target = os.path.join(OZ_PATH, "contracts/proxy/transparent/TransparentUpgradeableProxy.sol")
    
    # We want to ensure that 'relative.json' is created in the CURRENT directory,
    # not in the OZ project root.
    out_file = "relative_test_output.json"
    if os.path.exists(out_file):
        os.remove(out_file)
        
    try:
        # Run the tool from the repo root
        cmd = [
            sys.executable, "-m", "sol_callgraph.launcher", 
            target, 
            "--format", "json", 
            "--out", out_file,
            "--depth", "1"
        ]
        result = subprocess.run(cmd, capture_output=True, text=True)
        
        assert result.returncode == 0
        # Check if the file exists in the current directory
        assert os.path.exists(out_file), f"Output file {out_file} was not found in the calling directory."
        
        # Verify it's valid JSON
        with open(out_file, 'r') as f:
            data = json.load(f)
            assert data["target"] == target or data["target"].endswith("TransparentUpgradeableProxy.sol")

    finally:
        if os.path.exists(out_file):
            os.remove(out_file)

@pytest.mark.skipif(not os.path.exists(OZ_PATH), reason="OpenZeppelin contracts not found")
def test_relative_out_path_dot():
    target = os.path.join(OZ_PATH, "contracts/proxy/transparent/TransparentUpgradeableProxy.sol")
    out_file = "relative_test_output.dot"
    if os.path.exists(out_file):
        os.remove(out_file)
        
    try:
        cmd = [
            sys.executable, "-m", "sol_callgraph.launcher", 
            target, 
            "--format", "dot", 
            "--out", out_file,
            "--depth", "1"
        ]
        result = subprocess.run(cmd, capture_output=True, text=True)
        
        assert result.returncode == 0
        assert os.path.exists(out_file)
        with open(out_file, 'r') as f:
            content = f.read()
            assert "digraph focused_call_graph" in content

    finally:
        if os.path.exists(out_file):
            os.remove(out_file)
