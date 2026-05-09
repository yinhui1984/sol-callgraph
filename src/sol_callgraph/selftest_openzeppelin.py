import os
import sys
import subprocess
import json
import time
import glob
from typing import List, Dict, Tuple, Optional

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

CORE_SAMPLES = [
    "contracts/proxy/transparent/TransparentUpgradeableProxy.sol",
    "contracts/proxy/ERC1967/ERC1967Utils.sol",
]

def run_cmd(cmd: List[str]) -> Tuple[int, str, str]:
    process = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    stdout, stderr = process.communicate()
    return process.returncode, stdout, stderr

def run_tool(args: List[str]) -> Tuple[int, str, str]:
    cmd = [sys.executable, "-m", "sol_callgraph.launcher"] + args
    return run_cmd(cmd)

def get_slither_version() -> str:
    rc, stdout, _ = run_cmd(["slither", "--version"])
    return stdout.strip() if rc == 0 else "unknown"

def get_git_commit(path: str) -> str:
    rc, stdout, _ = run_cmd(["git", "-C", path, "rev-parse", "HEAD"])
    return stdout.strip() if rc == 0 else "unknown"

def discover_samples(oz_path: str, max_samples: int = 30) -> List[str]:
    pattern = os.path.join(oz_path, "contracts/**/*.sol")
    all_files = glob.glob(pattern, recursive=True)
    
    # Simple selection: avoid mocks and select some from key dirs
    samples = []
    seen_dirs = {}
    
    # Prioritize non-mock
    filtered = [f for f in all_files if "/mocks/" not in f]
    
    for f in filtered:
        rel_path = os.path.relpath(f, oz_path)
        if rel_path in FIXED_SAMPLES:
            continue
            
        dir_name = os.path.dirname(rel_path)
        if seen_dirs.get(dir_name, 0) < 2:
            samples.append(rel_path)
            seen_dirs[dir_name] = seen_dirs.get(dir_name, 0) + 1
            
        if len(samples) >= max_samples:
            break
    return samples

def count_nodes_edges(dot_content: str) -> Tuple[int, int]:
    nodes = 0
    edges = 0
    for line in dot_content.splitlines():
        if "->" in line:
            edges += 1
        elif "[" in line and "rankdir" not in line and "node [" not in line and "edge [" not in line:
            nodes += 1
    return nodes, edges

def check_tup_edges(dot_content: str) -> bool:
    # Relaxed check for TUP edges to handle stable IDs and metadata
    check1 = '_dispatchUpgradeToAndCall()" -> "contracts/proxy/ERC1967/ERC1967Utils.sol::ERC1967Utils::upgradeToAndCall'
    check2 = '_dispatchUpgradeToAndCall()" -> "abi.decode()"'
    return check1 in dot_content and check2 in dot_content

def classify_result(rc_dot: int, err_dot: str, rc_list: int, dot_valid: str, extra_check: str) -> str:
    """
    Classifies the result of a single sample test.
    Returns 'PASS', 'FAIL', or 'EXPECTED_NO_ROOT'.
    """
    if rc_dot == 3 and "no root functions found" in err_dot.lower():
        return "EXPECTED_NO_ROOT"
    
    if rc_dot == 0 and rc_list == 0 and dot_valid == "OK":
        if extra_check == "FAIL":
            return "FAIL"
        return "PASS"
    
    return "FAIL"

def main():
    oz_path = os.environ.get("OZ_CONTRACTS_DIR", OZ_DEFAULT_PATH)
    if not os.path.exists(oz_path):
        print(f"error: OpenZeppelin contracts not found at {oz_path}", file=sys.stderr)
        sys.exit(1)

    os.makedirs(ARTIFACTS_DIR, exist_ok=True)
    
    slither_ver = get_slither_version()
    oz_commit = get_git_commit(oz_path)
    
    discovered = discover_samples(oz_path)
    all_test_samples = FIXED_SAMPLES + discovered
    
    results = []
    
    print(f"Running self-test on {oz_path} ({len(all_test_samples)} samples)...")

    for sample in all_test_samples:
        target = os.path.join(oz_path, sample)
        print(f"[{len(results)+1}/{len(all_test_samples)}] Testing {sample}:", flush=True)
        
        depth = 2 if sample in CORE_SAMPLES else 1
        
        # 1. list-contracts
        print("  - Listing contracts...", end=" ", flush=True)
        rc_list, _, _ = run_tool([target, "--list-contracts"])
        print("Done." if rc_list == 0 else "FAIL")
        
        # 2. dot output
        print(f"  - Generating DOT (depth {depth})...", end=" ", flush=True)
        start_time = time.time()
        rc_dot, out_dot, err_dot = run_tool([target, "--depth", str(depth)])
        elapsed = time.time() - start_time
        print(f"Done ({elapsed:.1f}s)." if rc_dot == 0 else f"RC {rc_dot}")
        
        nodes, edges = 0, 0
        dot_valid = "FAIL" if rc_dot == 0 else "N/A"
        extra_check = "N/A"
        
        if rc_dot == 0:
            nodes, edges = count_nodes_edges(out_dot)
            # Validate DOT via Graphviz
            print("  - Validating DOT with Graphviz...", end=" ", flush=True)
            dot_path = os.path.join(ARTIFACTS_DIR, f"{os.path.basename(sample)}.dot")
            with open(dot_path, "w") as f: f.write(out_dot)
            rc_gv, _, _ = run_cmd(["dot", "-Tsvg", dot_path, "-o", "/dev/null"])
            dot_valid = "OK" if rc_gv == 0 else "FAIL"
            print(dot_valid)
            
            if "TransparentUpgradeableProxy.sol" in sample:
                print("  - Verifying TUP critical edges...", end=" ", flush=True)
                extra_check = "PASS" if check_tup_edges(out_dot) else "FAIL"
                print(extra_check)
        
        status = classify_result(rc_dot, err_dot, rc_list, dot_valid, extra_check)
        print(f"  Result: {status}")
        
        res = {
            "sample": sample,
            "depth": depth,
            "rc_list": rc_list,
            "rc_dot": rc_dot,
            "dot_valid": dot_valid,
            "extra_check": extra_check,
            "nodes": nodes,
            "edges": edges,
            "status": status
        }
        results.append(res)

    # Filter real failures
    failures = [r for r in results if r["status"] == "FAIL"]
    pass_count = len([r for r in results if r["status"] == "PASS"])
    no_root_count = len([r for r in results if r["status"] == "EXPECTED_NO_ROOT"])

    # Write artifacts
    with open(os.path.join(ARTIFACTS_DIR, "selected-samples.txt"), "w") as f:
        f.write("\n".join(all_test_samples))
    
    with open(os.path.join(ARTIFACTS_DIR, "failures.json"), "w") as f:
        json.dump(failures, f, indent=2)

    # Generate Report
    report_path = os.path.join(ARTIFACTS_DIR, "report.md")
    with open(report_path, "w") as f:
        f.write("# sol-callgraph OpenZeppelin Self-test Report\n\n")
        f.write(f"- **Date**: {time.strftime('%Y-%m-%d %H:%M:%S')}\n")
        f.write(f"- **OZ Path**: {oz_path}\n")
        f.write(f"- **OZ Commit**: {oz_commit}\n")
        f.write(f"- **Slither Version**: {slither_ver}\n\n")
        
        f.write("## Summary\n\n")
        f.write(f"- **Total**: {len(results)}\n")
        f.write(f"- **Pass**: {pass_count}\n")
        f.write(f"- **Expected no root**: {no_root_count}\n")
        f.write(f"- **Failures**: {len(failures)}\n\n")
        
        f.write("## Results\n\n")
        f.write("| Sample | Depth | List | DOT | Valid | Check | Nodes | Edges | Status |\n")
        f.write("| --- | --- | --- | --- | --- | --- | --- | --- | --- |\n")
        for res in results:
            val_display = "N/A" if res["status"] == "EXPECTED_NO_ROOT" else res["dot_valid"]
            f.write(f"| {res['sample']} | {res['depth']} | {res['rc_list']} | {res['rc_dot']} | {val_display} | {res['extra_check']} | {res['nodes']} | {res['edges']} | {res['status']} |\n")

    print(f"\nSelf-test complete. Total: {len(results)}, Pass: {pass_count}, No Root: {no_root_count}, Failures: {len(failures)}")
    print(f"Report: {report_path}")

    if failures:
        sys.exit(1)
    else:
        sys.exit(0)

if __name__ == "__main__":
    main()
