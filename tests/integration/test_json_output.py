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

def test_json_source_location_disambiguates_interface_and_implementation(tmp_path):
    fixture = tmp_path / "StakedTokenV2Rev4.sol"
    fixture.write_text("""interface IStakedAave {
  function stake(address to, uint256 amount) external;

  function redeem(address to, uint256 amount) external;

  function cooldown() external;

  function claimRewards(address to, uint256 amount) external;
}

contract GovernancePowerWithSnapshot {}
contract VersionedInitializable {}
contract AaveDistributionManager {}

contract StakedTokenV2Rev4 is
  IStakedAave,
  GovernancePowerWithSnapshot,
  VersionedInitializable,
  AaveDistributionManager {
  function stake(address to, uint256 amount) external {}

  function redeem(address to, uint256 amount) external {}

  function cooldown() external {}

  function claimRewards(address to, uint256 amount) external {}
}
""")

    cmd = [
        sys.executable,
        "-m",
        "sol_callgraph.launcher",
        str(fixture),
        "--include-interfaces",
        "--format",
        "json",
    ]
    result = subprocess.run(cmd, capture_output=True, text=True)

    assert result.returncode == 0, result.stderr
    data = json.loads(result.stdout)
    nodes = {node["id"]: node for node in data["nodes"]}

    interface_node = nodes["StakedTokenV2Rev4.sol::IStakedAave::redeem(address,uint256)"]
    implementation_node = nodes["StakedTokenV2Rev4.sol::StakedTokenV2Rev4::redeem(address,uint256)"]

    assert interface_node["declared_contract"] == "IStakedAave"
    assert implementation_node["declared_contract"] == "StakedTokenV2Rev4"
    assert interface_node["source_location"]["path"] == "StakedTokenV2Rev4.sol"
    assert implementation_node["source_location"]["path"] == "StakedTokenV2Rev4.sol"
    assert interface_node["source_location"]["start_line"] == 4
    assert implementation_node["source_location"]["start_line"] == 22

def test_json_definition_index_maps_call_reference_to_definition(tmp_path):
    fixture = tmp_path / "DefinitionProbe.sol"
    source = """contract DefinitionProbe {
  function target(uint256 amount) internal {}

  function caller() external {
    target(1);
  }
}
"""
    fixture.write_text(source)

    cmd = [
        sys.executable,
        "-m",
        "sol_callgraph.launcher",
        str(fixture),
        "--format",
        "json",
    ]
    result = subprocess.run(cmd, capture_output=True, text=True)

    assert result.returncode == 0, result.stderr
    data = json.loads(result.stdout)
    references = data["definition_index"]["references"]
    target_refs = [ref for ref in references if ref["name"] == "target"]

    assert len(target_refs) == 1
    reference = target_refs[0]
    assert reference["confidence"] == "exact"
    assert reference["source_location"]["start_line"] == 5
    assert reference["source_location"]["start_offset"] == source.index("target(1)")
    assert reference["definition_location"]["start_line"] == 2
    assert reference["definition_symbol_id"].endswith("::DefinitionProbe::target(uint256)")

    symbols = data["symbol_index"]["symbols"]
    target_symbols = [symbol for symbol in symbols if symbol["name"] == "target"]
    assert len(target_symbols) == 1
    assert target_symbols[0]["source_location"]["start_line"] == 2
