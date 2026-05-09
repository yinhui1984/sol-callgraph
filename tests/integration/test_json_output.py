import subprocess
import sys
import os
import json

def test_json_output():
    target = "tests/fixtures/Simple.sol"
    cmd = [sys.executable, "-m", "sol_callgraph.launcher", target, "--format", "json"]
    result = subprocess.run(cmd, capture_output=True, text=True)
    
    assert result.returncode == 0
    data = json.loads(result.stdout)
    assert data["schema_version"] == "0.1.0"
    assert data["target"] == target
    assert "nodes" in data
    assert "edges" in data
    
    # Check for foo and bar nodes
    node_labels = [n["label"] for n in data["nodes"]]
    assert "foo()" in node_labels
    assert "bar()" in node_labels
    
    # Check for edge
    edge_kinds = [e["kind"] for e in data["edges"]]
    assert "internal" in edge_kinds
