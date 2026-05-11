import subprocess
import sys
import os
import json

def test_debug_slither():
    target = "tests/fixtures/Simple.sol"
    cmd = [sys.executable, "-m", "sol_callgraph.launcher", target, "--debug-slither", "--solc-args=--optimize"]
    result = subprocess.run(cmd, capture_output=True, text=True)
    
    assert result.returncode == 0
    assert "DEBUG: slither invocation" in result.stderr
    assert f"target: {target}" in result.stderr
    assert "solc_args: --optimize" in result.stderr

def test_slither_arg_graph_attributes_in_dot():
    target = "tests/fixtures/Simple.sol"
    cmd = [
        sys.executable, "-m", "sol_callgraph.launcher", target,
        "--slither-arg=--graph-attributes",
        "--slither-arg=nodesep=0.8 ranksep=1.2 pad=0.5",
        "--slither-arg=--node-attributes",
        "--slither-arg=margin=0.6,0.1 fontsize=14 fontname=Courier",
    ]
    result = subprocess.run(cmd, capture_output=True, text=True)

    assert result.returncode == 0
    assert 'nodesep="0.8";' in result.stdout
    assert 'ranksep="1.2";' in result.stdout
    assert 'pad="0.5";' in result.stdout
    assert 'fontname="Courier"' in result.stdout
    assert 'margin="0.6,0.1"' in result.stdout

def test_slither_arg_graph_attributes_in_json():
    target = "tests/fixtures/Simple.sol"
    cmd = [
        sys.executable, "-m", "sol_callgraph.launcher", target,
        "--format", "json",
        "--slither-arg=--graph-attributes",
        "--slither-arg=nodesep=0.8 ranksep=1.2 pad=0.5",
    ]
    result = subprocess.run(cmd, capture_output=True, text=True)

    assert result.returncode == 0
    data = json.loads(result.stdout)
    assert data["render"]["graph_attributes"] == {
        "nodesep": "0.8",
        "ranksep": "1.2",
        "pad": "0.5",
    }

def test_unsupported_slither_cli_flag_errors():
    target = "tests/fixtures/Simple.sol"
    cmd = [
        sys.executable, "-m", "sol_callgraph.launcher", target,
        "--slither-arg=--unknown-flag",
    ]
    result = subprocess.run(cmd, capture_output=True, text=True)

    assert result.returncode == 1
    assert "unsupported Slither CLI flag" in result.stderr
