import sys
import os
import json
from slither import Slither
from slither.core.declarations import Contract, Function, Modifier
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
from sol_callgraph.slither_env import augment_process_path

def _path_relative_to_root(file_path, root):
    try:
        abs_path = os.path.realpath(file_path)
        root_path = os.path.realpath(root)
        if os.path.commonpath([abs_path, root_path]) == root_path:
            return os.path.relpath(abs_path, root_path)
        return os.path.basename(abs_path)
    except Exception:
        return file_path

def _get_source_location(obj, root):
    if not obj or not hasattr(obj, "source_mapping") or not obj.source_mapping:
        return None

    source_mapping = obj.source_mapping
    try:
        filename = source_mapping.filename.absolute
    except Exception:
        return None

    absolute_path = os.path.realpath(filename)
    lines = list(getattr(source_mapping, "lines", []) or [])
    start_offset = getattr(source_mapping, "start", None)
    length = getattr(source_mapping, "length", None)
    end_offset = getattr(source_mapping, "end", None)

    location = {
        "path": _path_relative_to_root(absolute_path, root),
        "absolute_path": absolute_path,
    }

    if lines:
        location["start_line"] = lines[0]
        location["end_line"] = lines[-1]
    if getattr(source_mapping, "starting_column", None) is not None:
        location["start_column"] = source_mapping.starting_column
    if getattr(source_mapping, "ending_column", None) is not None:
        location["end_column"] = source_mapping.ending_column
    if start_offset is not None:
        location["start_offset"] = start_offset
    if length is not None:
        location["length"] = length
    if end_offset is not None:
        location["end_offset"] = end_offset

    return location

def _symbol_kind(obj):
    kind = obj.__class__.__name__.lower()
    if isinstance(obj, Function):
        return "modifier" if isinstance(obj, Modifier) else "function"
    if isinstance(obj, Contract):
        return obj.contract_kind or "contract"
    return kind

def _source_snippet(location):
    absolute_path = location.get("absolute_path")
    start_offset = location.get("start_offset")
    length = location.get("length")
    if not absolute_path or start_offset is None or length is None:
        return None
    try:
        with open(absolute_path, "r", encoding="utf-8") as source_file:
            return source_file.read()[start_offset:start_offset + length]
    except Exception:
        return None

def _get_reference_location(ir, root):
    expression = getattr(ir, "expression", None)
    called = getattr(expression, "called", None)
    location = _get_source_location(called, root) if called else None
    if location:
        return location
    location = _get_source_location(expression, root) if expression else None
    if location:
        return location
    return _get_source_location(getattr(ir, "node", None), root)

def _build_symbol_index(sl, cg, target, root):
    symbols = []
    seen = set()
    declarations = list(sl.contracts)
    for contract in sl.contracts:
        declarations.extend(getattr(contract, "functions_and_modifiers_declared", []) or [])

    for obj in declarations:
        location = _get_source_location(obj, root)
        if not location:
            continue
        symbol_id = cg._get_node_id(obj) if isinstance(obj, (Function, Modifier)) else f"{location['path']}::{getattr(obj, 'name', str(obj))}"
        if symbol_id in seen:
            continue
        seen.add(symbol_id)
        container_path = []
        if hasattr(obj, "contract_declarer") and obj.contract_declarer:
            container_path.append(obj.contract_declarer.name)
        elif hasattr(obj, "contract") and obj.contract:
            container_path.append(obj.contract.name)

        symbol = {
            "id": symbol_id,
            "kind": _symbol_kind(obj),
            "name": getattr(obj, "name", str(obj)),
            "container_path": container_path,
            "source_location": location,
        }
        if hasattr(obj, "full_name"):
            symbol["signature"] = obj.full_name
        snippet = _source_snippet(location)
        if snippet:
            symbol["declaration_text"] = snippet
        symbols.append(symbol)

    return {
        "schema_version": 1,
        "target_path": target,
        "project_root": root,
        "symbols": symbols,
    }

def _build_definition_index(sl, cg, target, root):
    references = []
    seen = set()

    for contract in sl.contracts:
        for func in getattr(contract, "functions_and_modifiers_declared", []) or []:
            for node in getattr(func, "nodes", []) or []:
                for ir in getattr(node, "irs", []) or []:
                    definition = getattr(ir, "function", None)
                    if not isinstance(definition, (Function, Modifier)):
                        continue
                    reference_location = _get_reference_location(ir, root)
                    definition_location = _get_source_location(definition, root)
                    if not reference_location or not definition_location:
                        continue
                    reference_id = "|".join([
                        reference_location.get("absolute_path", reference_location.get("path", "")),
                        str(reference_location.get("start_offset", "")),
                        str(reference_location.get("length", "")),
                        cg._get_node_id(definition),
                    ])
                    if reference_id in seen:
                        continue
                    seen.add(reference_id)
                    references.append({
                        "id": reference_id,
                        "name": getattr(definition, "name", str(definition)),
                        "source_location": reference_location,
                        "definition_symbol_id": cg._get_node_id(definition),
                        "definition_location": definition_location,
                        "confidence": "exact",
                    })

    return {
        "schema_version": 1,
        "target_path": target,
        "project_root": root,
        "references": references,
    }

def main():
    augment_process_path()
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
        print(f"  slither_kwargs: {config.slither_kwargs}", file=sys.stderr)
        print(f"  graph_attributes: {config.graph_attributes}", file=sys.stderr)
        print(f"  node_attributes: {config.node_attributes}", file=sys.stderr)
        print(f"  edge_attributes: {config.edge_attributes}", file=sys.stderr)
        print(f"  solc_remaps: {config.solc_remaps}", file=sys.stderr)
        print(f"  solc_args: {config.solc_args}", file=sys.stderr)
        print(f"  compile_force_framework: {config.compile_force_framework}", file=sys.stderr)

    try:
        # Build Slither constructor arguments
        slither_kwargs = dict(config.slither_kwargs)
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

    # Prepare edges with semantic/rendering properties for consistency
    processed_edges = []
    for src, dst, kind, tooltip in cg.edges:
        style = "solid"
        constraint = True
        classes_str = f"edge-{kind}"
        
        if kind == "override":
            style = "dashed"
            constraint = False
            classes_str += " semantic non-execution"
            
        processed_edges.append({
            "src": src,
            "dst": dst,
            "kind": kind,
            "tooltip": tooltip,
            "style": style,
            "constraint": constraint,
            "classes": classes_str.split()
        })

    renderer = DotRenderer(
        graph_attrs=config.graph_attributes,
        node_attrs=config.node_attributes,
        edge_attrs=config.edge_attributes,
    )
    for node_id, data in cg.nodes.items():
        format_node(renderer, node_id, data["label"], data["type"], 
                    classes=data.get("classes"), tooltip=data.get("tooltip"),
                    cluster=data.get("cluster"))
    
    for edge in processed_edges:
        renderer.add_edge(
            edge["src"], edge["dst"], label=edge["kind"], 
            class_attr=" ".join(edge["classes"]), tooltip=edge["tooltip"],
            style=None if edge["style"] == "solid" else edge["style"], 
            constraint=edge["constraint"]
        )
    
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
            "render": {
                "graph_attributes": config.graph_attributes,
                "node_attributes": config.node_attributes,
                "edge_attributes": config.edge_attributes
            },
            "symbol_index": _build_symbol_index(sl, cg, config.target, os.getcwd()),
            "definition_index": _build_definition_index(sl, cg, config.target, os.getcwd()),
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
                source_location = _get_source_location(obj, os.getcwd())
                if source_location:
                    node_info["source_location"] = source_location
                if hasattr(obj, 'contract_declarer') and obj.contract_declarer:
                    node_info["declared_contract"] = obj.contract_declarer.name
                    node_info["declared_contract_kind"] = obj.contract_declarer.contract_kind
                if hasattr(obj, 'contract') and obj.contract:
                    node_info["contract"] = obj.contract.name
                    node_info["contract_kind"] = obj.contract.contract_kind
                    node_info["viewed_as_contract"] = obj.contract.name
                if hasattr(obj, 'visibility'):
                    node_info["visibility"] = obj.visibility
                if hasattr(obj, 'full_name'):
                    node_info["signature"] = obj.full_name
            output_data["nodes"].append(node_info)
            
        for edge in processed_edges:
            output_data["edges"].append({
                "src": edge["src"],
                "dst": edge["dst"],
                "kind": edge["kind"],
                "classes": edge["classes"],
                "style": edge["style"],
                "constraint": edge["constraint"],
                "tooltip": edge["tooltip"]
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
