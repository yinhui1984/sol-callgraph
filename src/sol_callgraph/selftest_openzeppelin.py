import os
import sys
import subprocess
import json
import time
from typing import List, Dict, Tuple

# Default path to OZ contracts
OZ_DEFAULT_PATH = "external/openzeppelin-contracts"
ARTIFACTS_DIR = "test-artifacts/openzeppelin-selftest"

FIXED_SAMPLES = [
    "contracts/proxy/transparent/TransparentUpgradeableProxy.sol",
    "contracts/proxy/ERC1967/ERC1967Utils.sol",
    "contracts/proxy/Clones.sol",
    "contracts/token/ERC20/ERC20.sol",
    "contracts/token/ERC20/utils/SafeERC20.sol",
    "contracts/token/ERC721/ERC721.sol",
    "contracts/token/ERC1155/ERC1155.sol",
    "contracts/access/Ownable.sol",
    "contracts/access/AccessControl.sol",
    "contracts/governance/Governor.sol",
]

def run_cmd(cmd: List[str]) -> Tuple[int, str, str]:
    process = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    stdout, stderr = process.communicate()
    return process.returncode, stdout, stderr

def run_tool(args: List[str]) -> Tuple[int, str, str]:
    # Use the current interpreter to run the launcher
    cmd = [sys.executable, "-m", "sol_callgraph.launcher"] + args
    return run_cmd(cmd)

def main():
    oz_path = os.environ.get("OZ_CONTRACTS_DIR", OZ_DEFAULT_PATH)
    if not os.path.exists(oz_path):
        print(f"error: OpenZeppelin contracts not found at {oz_path}")
        sys.exit(1)

    os.makedirs(ARTIFACTS_DIR, exist_ok=True)
    report_path = os.path.join(ARTIFACTS_DIR, "report.md")
    
    results = []
    
    print(f"Running self-test on {oz_path}...")

    for sample in FIXED_SAMPLES:
        target = os.path.join(oz_path, sample)
        if not os.path.exists(target):
            results.append({"sample": sample, "status": "SKIP", "reason": "File not found"})
            continue
        
        print(f"Testing {sample}...")
        
        # 1. list-contracts
        rc_list, out_list, err_list = run_tool([target, "--list-contracts"])
        
        # 2. depth 1 dot
        dot_file = os.path.join(ARTIFACTS_DIR, f"{os.path.basename(sample)}.depth1.dot")
        rc_dot, out_dot, err_dot = run_tool([target, "--depth", "1", "-o", dot_file])
        
        # Validate DOT via Graphviz (if available)
        dot_valid = "N/A"
        if rc_dot == 0:
            rc_gv, _, _ = run_cmd(["dot", "-Tsvg", dot_file])
            dot_valid = "OK" if rc_gv == 0 else "FAIL"

        # Check for TransparentUpgradeableProxy specific edge
        extra_check = "N/A"
        if "TransparentUpgradeableProxy.sol" in sample and rc_dot == 0:
            with open(dot_file, 'r') as f:
                content = f.read()
                has_edge = 'ERC1967Utils.upgradeToAndCall(address,bytes)' in content
                extra_check = "PASS" if has_edge else "FAIL"

        results.append({
            "sample": sample,
            "rc_list": rc_list,
            "rc_dot": rc_dot,
            "dot_valid": dot_valid,
            "extra_check": extra_check,
            "status": "PASS" if rc_dot == 0 and rc_list == 0 else "FAIL"
        })

    # Generate Markdown Report
    with open(report_path, "w") as f:
        f.write("# sol-callgraph OpenZeppelin Self-test Report\n\n")
        f.write(f"Date: {time.strftime('%Y-%m-%d %H:%M:%S')}\n")
        f.write(f"OZ Path: {oz_path}\n\n")
        
        f.write("| Sample | List | DOT | Valid | Check | Status |\n")
        f.write("| --- | --- | --- | --- | --- | --- |\n")
        for res in results:
            f.write(f"| {res['sample']} | {res.get('rc_list', '-')} | {res.get('rc_dot', '-')} | {res.get('dot_valid', '-')} | {res.get('extra_check', '-')} | {res['status']} |\n")

    print(f"Self-test complete. Report: {report_path}")

if __name__ == "__main__":
    from typing import Tuple # Ensure Tuple is imported
    main()
