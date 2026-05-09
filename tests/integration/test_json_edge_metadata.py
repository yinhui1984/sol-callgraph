import subprocess
import sys
import os
import json
import pytest

def test_json_edge_metadata_standard():
    target = "tests/fixtures/Simple.sol"
    cmd = [sys.executable, "-m", "sol_callgraph.launcher", target, "--format", "json"]
    result = subprocess.run(cmd, capture_output=True, text=True)
    
    assert result.returncode == 0
    data = json.loads(result.stdout)
    
    # Simple.sol has an internal call from foo to bar
    internal_edges = [e for e in data["edges"] if e["kind"] == "internal"]
    assert len(internal_edges) > 0
    edge = internal_edges[0]
    
    assert "classes" in edge
    assert "edge-internal" in edge["classes"]
    assert edge["style"] == "solid"
    assert edge["constraint"] is True
    assert "tooltip" in edge

def test_json_edge_metadata_override():
    fixture = "tests/fixtures/Overrides_JSON.sol"
    with open(fixture, "w") as f:
        f.write("""
contract Base {
    function foo() public virtual {}
}
contract Child is Base {
    function foo() public override {}
}
""")
    try:
        cmd = [sys.executable, "-m", "sol_callgraph.launcher", fixture, "--contract", "Child", "--include-overrides", "--format", "json"]
        result = subprocess.run(cmd, capture_output=True, text=True)
        
        assert result.returncode == 0
        data = json.loads(result.stdout)
        
        override_edges = [e for e in data["edges"] if e["kind"] == "override"]
        assert len(override_edges) > 0
        edge = override_edges[0]
        
        assert "classes" in edge
        assert "edge-override" in edge["classes"]
        assert "semantic" in edge["classes"]
        assert "non-execution" in edge["classes"]
        assert edge["style"] == "dashed"
        assert edge["constraint"] is False
        assert "non-execution" in edge["tooltip"]
        
    finally:
        if os.path.exists(fixture):
            os.remove(fixture)

def test_dot_json_consistency():
    target = "tests/fixtures/Simple.sol"
    
    # Get JSON
    cmd_json = [sys.executable, "-m", "sol_callgraph.launcher", target, "--format", "json"]
    data = json.loads(subprocess.run(cmd_json, capture_output=True, text=True).stdout)
    
    # Get DOT
    cmd_dot = [sys.executable, "-m", "sol_callgraph.launcher", target, "--format", "dot"]
    dot = subprocess.run(cmd_dot, capture_output=True, text=True).stdout
    
    # Compare internal edge properties
    json_edge = [e for e in data["edges"] if e["kind"] == "internal"][0]
    
    # DOT should have class="edge-internal"
    assert 'class="edge-internal"' in dot
    # For solid edges, we omit style in DOT to keep it clean, but JSON should have "solid"
    assert 'style="solid"' not in dot # Expected behavior: solid is default in DOT
    assert json_edge["style"] == "solid"
    
    # Check constraint
    assert 'constraint=false' not in dot # Default is true in DOT
    assert json_edge["constraint"] is True
