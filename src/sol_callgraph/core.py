import sys
import os
import json
from slither import Slither
try:
    from slither import __version__ as slither_version
except ImportError:
    slither_version = "unknown"
except AttributeError:
    slither_version = "unknown"
from sol_callgraph.cli import parse_args
from sol_callgraph.graph import CallGraph
from sol_callgraph.dot import DotRenderer, format_node
from sol_callgraph.graphviz import run_dot

def main():
    config = parse_args(sys.argv[1:])
    
    if not config.target and not config.list_contracts:
        from sol_callgraph.cli import T
        sys.stderr.write(f"{T['error']}: {T['err_no_target']}\n\n")
        config.parser.print_help()
        sys.exit(1)

    if not os.path.exists(config.target):
        from sol_callgraph.cli import T
        print(f"{T['error']}: target file not found: {config.target}", file=sys.stderr)
        sys.exit(3)

    if config.debug_slither:
        print(f"DEBUG: slither invocation", file=sys.stderr)
        print(f"  cwd: {os.getcwd()}", file=sys.stderr)
        print(f"  target: {config.target}", file=sys.stderr)
        print(f"  slither_args: {config.slither_args}", file=sys.stderr)
        print(f"  solc_remaps: {config.solc_remaps}", file=sys.stderr)
        print(f"  solc_args: {config.solc_args}", file=sys.stderr)
        print(f"  compile_force_framework: {config.compile_force_framework}", file=sys.stderr)

    try:
        # Build Slither constructor arguments
        slither_kwargs = {}
        if config.solc_remaps:
            slither_kwargs["solc_remaps"] = config.solc_remaps.split()
        if config.solc_args:
            slither_kwargs["solc_args"] = config.solc_args
        if config.compile_force_framework:
            slither_kwargs["compile_force_framework"] = config.compile_force_framework
            
        sl = Slither(config.target, **slither_kwargs)
    except Exception as e:
        print(f"error: Slither/solc failed to parse {config.target}: {e}", file=sys.stderr)
        sys.exit(2)

    if config.list_contracts:
        target_abs_path = os.path.realpath(config.target)
        for c in sl.contracts:
            if hasattr(c, 'source_mapping') and c.source_mapping:
                try:
                    filename = os.path.realpath(c.source_mapping.filename.absolute)
                    if filename == target_abs_path:
                        print(f"{c.name:<30} {c.contract_kind}")
                except:
                    pass
        sys.exit(0)

    cg = CallGraph(sl, config)
    
    # Task 2: Fix --contract not found error handling
    if config.contracts:
        target_abs_path = os.path.realpath(config.target)
        available_decls = []
        for c in sl.contracts:
            try:
                if os.path.realpath(c.source_mapping.filename.absolute) == target_abs_path:
                    available_decls.append(c)
            except: pass
            
        for c_name in config.contracts:
            if not any(c.name == c_name for c in sl.contracts):
                print(f"error: contract {c_name} not found in {config.target}", file=sys.stderr)
                print("Available declarations:", file=sys.stderr)
                for c in available_decls:
                    print(f"  {c.name:<20} {c.contract_kind}", file=sys.stderr)
                sys.exit(3)

    if not cg.build():
        print(f"error: no root functions found in {config.target}", file=sys.stderr)
        sys.exit(3)

    renderer = DotRenderer()
    for node_id, data in cg.nodes.items():
        format_node(renderer, node_id, data["label"], data["type"], 
                    classes=data.get("classes"), tooltip=data.get("tooltip"),
                    cluster=data.get("cluster"))
    
    for src, dst, kind, tooltip in cg.edges:
        renderer.add_edge(src, dst, label=kind, class_attr=f"edge-{kind}", tooltip=tooltip)
    
    dot_content = renderer.render()

    if config.format == "json":
        # Task 11: JSON output
        output_data = {
            "schema_version": "0.1.0",
            "target": config.target,
            "project_root": os.getcwd(),
            "tool_version": "0.1.0",
            "slither_version": slither_version,
            "stats": {
                "nodes": len(cg.nodes),
                "edges": len(cg.edges),
                "unresolved": cg.unresolved_stats
            },
            "nodes": [],
            "edges": []
        }
        
        for node_id, data in cg.nodes.items():
            node_info = {
                "id": node_id,
                "label": data["label"],
                "role": data["type"],
                "classes": data.get("classes", "").split(),
                "tooltip": data.get("tooltip")
            }
            # Add more detail if object is available
            obj = data.get("obj")
            if obj:
                if hasattr(obj, 'contract') and obj.contract:
                    node_info["contract"] = obj.contract.name
                    node_info["contract_kind"] = obj.contract.contract_kind
                if hasattr(obj, 'visibility'):
                    node_info["visibility"] = obj.visibility
                if hasattr(obj, 'full_name'):
                    node_info["signature"] = obj.full_name
            output_data["nodes"].append(node_info)
            
        for src, dst, kind, tooltip in cg.edges:
            output_data["edges"].append({
                "src": src,
                "dst": dst,
                "kind": kind,
                "tooltip": tooltip
            })
            
        json_output = json.dumps(output_data, indent=2)
        if config.out:
            try:
                with open(config.out, 'w', encoding='utf-8') as f:
                    f.write(json_output)
            except Exception as e:
                print(f"error: failed to write output file: {e}", file=sys.stderr)
                sys.exit(4)
        else:
            print(json_output)
            
    elif config.format == "dot":
        if config.out:
            try:
                with open(config.out, 'w', encoding='utf-8') as f:
                    f.write(dot_content)
            except Exception as e:
                print(f"error: failed to write output file: {e}", file=sys.stderr)
                sys.exit(4)
        else:
            print(dot_content)
    else:
        # Task 3: SVG or PNG
        if config.out:
            run_dot(dot_content, config.format, config.out)
        else:
            binary_output = run_dot(dot_content, config.format)
            if binary_output:
                sys.stdout.buffer.write(binary_output)

    # Task 9: Size Protection & Diagnostics
    if config.fail_on_unresolved and any(v > 0 for v in cg.unresolved_stats.values()):
        print("error: unresolved calls found and --fail-on-unresolved is set", file=sys.stderr)
        sys.exit(1)
        
    if config.fail_on_warning and cg.warnings:
        print("error: warnings found and --fail-on-warning is set", file=sys.stderr)
        sys.exit(1)
        
    sys.exit(0)

if __name__ == "__main__":
    main()
