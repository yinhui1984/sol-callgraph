import os
import sys
from collections import deque
from typing import List, Set, Dict, Any, Optional, Tuple
from slither.core.declarations import Contract, Function, Modifier
from slither.slithir.operations import SolidityCall, LibraryCall, HighLevelCall, LowLevelCall, EventCall

class CallGraph:
    def __init__(self, slither, config):
        self.sl = slither
        self.config = config
        self.nodes = {}  # id -> {label, type, obj, classes, tooltip, cluster}
        self.edges = set()  # (src_id, dst_id, kind, tooltip)
        self.processed_functions = set()
        self.root_functions = set()
        self.warnings = []
        self.unresolved_stats = {"low_level": 0, "high_level": 0, "library": 0, "solidity": 0}

    def _get_node_id(self, obj):
        """Generates a stable node ID: source_unit::contract::function_signature"""
        if not obj:
            return "unknown"
        if isinstance(obj, (Function, Modifier)):
            source = "unknown"
            try:
                source = obj.source_mapping.filename.absolute
                # Make it relative to root for stability
                root = getattr(self.config, 'root', None) or os.getcwd()
                if source.startswith(root):
                    source = os.path.relpath(source, root)
                else:
                    source = os.path.basename(source)
            except: pass
            
            contract_name = "top_level"
            if hasattr(obj, 'contract_declarer') and obj.contract_declarer:
                contract_name = obj.contract_declarer.name
            elif hasattr(obj, 'contract') and obj.contract:
                contract_name = obj.contract.name
                
            return f"{source}::{contract_name}::{obj.full_name}"
        return str(obj)

    def build(self):
        self._select_root_functions()
        if not self.root_functions:
            return False

        queue = deque([(f, 0) for f in self.root_functions])
        seen = {self._get_node_id(f) for f in self.root_functions}

        # Root functions/modifiers
        target_abs_path = os.path.realpath(self.config.target)
        for f in self.root_functions:
            if self.config.max_nodes > 0 and len(self.nodes) >= self.config.max_nodes:
                self.warnings.append(f"Reached max nodes limit ({self.config.max_nodes}). Graph truncated.")
                break
            
            node_id = self._get_node_id(f)
            node_type = "root"
            classes = self._get_node_classes(f, "root")
            
            is_inherited = False
            if self.config.contracts:
                declarer_name = f.canonical_name.split('.')[0]
                if not any(declarer_name == c_name for c_name in self.config.contracts):
                    is_inherited = True
            elif not self._is_in_target_file(f, target_abs_path):
                is_inherited = True
                
            if is_inherited:
                classes.append("inherited")
            
            tooltip = self._get_node_tooltip(f, classes)
            self._add_node(node_id, self._get_label(f), node_type, f, classes=" ".join(classes), tooltip=tooltip)

        edge_count = 0
        while queue:
            func, depth = queue.popleft()
            src_id = self._get_node_id(func)
            
            if depth >= self.config.depth:
                continue

            # Check limits
            if self.config.max_nodes > 0 and len(self.nodes) >= self.config.max_nodes:
                self.warnings.append(f"Reached max nodes limit ({self.config.max_nodes}). Graph truncated.")
                break
            if self.config.max_edges > 0 and len(self.edges) >= self.config.max_edges:
                self.warnings.append(f"Reached max edges limit ({self.config.max_edges}). Graph truncated.")
                break

            # Collect edges
            edges = self._collect_edges(func)
            for dst_id_raw, dst_label, kind, dst_obj in edges:
                dst_id = self._get_node_id(dst_obj) if dst_obj else dst_id_raw
                
                # Track unresolved stats
                if not dst_obj:
                    if kind in self.unresolved_stats:
                        self.unresolved_stats[kind] += 1
                
                edge_tooltip = f"kind: {kind}"
                if dst_obj: edge_tooltip += ", resolved: yes"
                else: edge_tooltip += ", resolved: no"
                
                self.edges.add((src_id, dst_id, kind, edge_tooltip))
                edge_count += 1
                
                # Check if we should expand dst
                if dst_obj and isinstance(dst_obj, (Function, Modifier)):
                    if dst_id not in seen:
                        seen.add(dst_id)
                        queue.append((dst_obj, depth + 1))
                        
                        if dst_id not in self.nodes:
                            classes = self._get_node_classes(dst_obj, "expandable")
                            tooltip = self._get_node_tooltip(dst_obj, classes)
                            self._add_node(dst_id, dst_label, "expandable", dst_obj, classes=" ".join(classes), tooltip=tooltip)
                else:
                    if dst_id not in self.nodes:
                        node_type = "builtin-like" if kind in ("solidity", "event", "error") else "unresolved"
                        self._add_node(dst_id, dst_label, node_type, dst_obj)

        if self.config.verbose:
            print(f"Graph built: {len(self.nodes)} nodes, {edge_count} edges", file=sys.stderr)
            print(f"Root functions: {len(self.root_functions)}", file=sys.stderr)
            print(f"Unresolved calls: {self.unresolved_stats}", file=sys.stderr)

        for w in self.warnings:
            print(f"warning: {w}", file=sys.stderr)

        return True

    def _get_node_tooltip(self, f, classes):
        info = []
        if hasattr(f, 'canonical_name'): info.append(f.canonical_name)
        if hasattr(f, 'visibility'): info.append(f"visibility: {f.visibility}")
        if hasattr(f, 'contract') and f.contract:
            kind = f.contract.contract_kind
            info.append(f"contract: {f.contract.name} ({kind})")
        info.append(f"classes: {', '.join(classes)}")
        return "\n".join(info)

    def _get_node_classes(self, f, role):
        classes = [role]
        if isinstance(f, Modifier):
            classes.append("modifier")
        else:
            classes.append("function")
            if f.is_constructor: classes.append("constructor")
            if f.is_fallback: classes.append("fallback")
            if f.is_receive: classes.append("receive")
            
            # Entrypoint marking
            if f.visibility in ("external", "public") or f.is_constructor or f.is_fallback or f.is_receive:
                classes.append("entrypoint")
            
            if f.visibility:
                classes.append(f.visibility)

            # Initializer detection
            if self._is_initializer(f):
                classes.append("initializer")
        return classes

    def _is_initializer(self, f):
        if not isinstance(f, Function):
            return False
        # Check name
        init_names = ["initialize", "reinitialize"]
        if any(name in f.name for name in init_names):
            return True
        if f.name.startswith("__") and "_init" in f.name:
            return True
        # Check modifiers
        if hasattr(f, 'modifiers'):
            for m in f.modifiers:
                if m.name in ("initializer", "reinitializer", "onlyInitializing"):
                    return True
        return False

    def _select_root_functions(self):
        target_abs_path = os.path.realpath(self.config.target)
        
        # Determine target contracts/declarations
        target_contracts = []
        if self.config.contracts:
            for c_name in self.config.contracts:
                found = False
                for c in self.sl.contracts:
                    if c.name == c_name:
                        target_contracts.append(c)
                        found = True
                        break
                if not found:
                    # Will be handled by core.py for exit 3
                    pass
        else:
            # Default to all contracts in target file
            in_file_contracts = []
            for c in self.sl.contracts:
                if self._is_in_target_file(c, target_abs_path):
                    in_file_contracts.append(c)
            
            if not self.config.quiet and len(in_file_contracts) > 1:
                decls = [f"{c.name}({c.contract_kind})" for c in in_file_contracts]
                msg = f"multiple declarations found in {self.config.target}: {', '.join(decls)}"
                self.warnings.append(msg)
                print(f"warning: {msg}", file=sys.stderr)
                msg2 = "using all executable declarations in target file as root scope; use --contract <name> to narrow it"
                print(f"warning: {msg2}", file=sys.stderr)

            for c in in_file_contracts:
                # Default rules: skip interfaces unless requested
                if c.contract_kind == "interface" and not self.config.include_interfaces:
                    continue
                target_contracts.append(c)

        # Collect functions from target contracts
        all_potential_roots = []
        for c in target_contracts:
            if self.config.include_inherited:
                # Use all visible functions (declared + inherited)
                funcs = c.functions_and_modifiers
            else:
                # ONLY declared functions and modifiers
                funcs = c.functions_and_modifiers_declared
            
            for f in funcs:
                # Filter by implementation and interface rules
                if not f.is_implemented and not self.config.include_interfaces:
                    continue
                
                # Phase 2: --no-constructors
                if self.config.no_constructors and f.is_constructor:
                    continue
                
                # If we are using file scope (no explicit contracts), 
                # we still want to limit to target file unless include_inherited is ON.
                # If include_inherited is ON, we allow them even if from other files.
                if not self.config.contracts and not self.config.include_inherited:
                    if not self._is_in_target_file(f, target_abs_path):
                        continue
                
                all_potential_roots.append(f)

        # Apply --root-function filtering if specified
        if self.config.root_function:
            filtered_roots = []
            for pattern in self.config.root_function:
                matches = self._find_functions_by_pattern(all_potential_roots, pattern)
                if len(matches) == 1:
                    filtered_roots.append(matches[0])
                elif len(matches) > 1:
                    print(f"error: function name `{pattern}` is ambiguous", file=os.sys.stderr)
                    print("candidates:", file=os.sys.stderr)
                    for m in matches:
                        print(f"  {m.canonical_name}", file=os.sys.stderr)
                    sys.exit(3)
                else:
                    print(f"warning: root function `{pattern}` not found", file=os.sys.stderr)
            self.root_functions = set(filtered_roots)
        else:
            self.root_functions = set(all_potential_roots)

    def _find_functions_by_pattern(self, functions, pattern):
        """Finds functions by canonical name or unique short name."""
        # Exact match on canonical name
        exact_matches = [f for f in functions if f.canonical_name == pattern]
        if exact_matches:
            return exact_matches
        
        # Match by Contract.function (without args)
        contract_func_matches = [f for f in functions if f.canonical_name.split('(')[0] == pattern]
        if contract_func_matches:
            return contract_func_matches
        
        # Match by name (short name, e.g., "_update")
        name_matches = [f for f in functions if f.name == pattern]
        return name_matches

    def _is_in_target_file(self, obj, target_abs_path):
        if not hasattr(obj, 'source_mapping') or not obj.source_mapping:
            return False
        # Some versions of slither have different structure for source_mapping
        # But usually we can get the filename
        try:
            filename = os.path.realpath(obj.source_mapping.filename.absolute)
            return filename == target_abs_path
        except:
            return False

    def _get_label(self, func):
        if func in self.root_functions:
            # Short name for root functions
            return func.name + "()"
        return func.canonical_name

    def _add_node(self, node_id, label, node_type, obj, classes=None, tooltip=None):
        if node_id not in self.nodes:
            if classes is None:
                classes = f"{node_type} function"
            
            cluster = None
            if self.config.cluster and obj and hasattr(obj, 'contract') and obj.contract:
                # Only cluster root declarations by default (Phase 2 suggestion)
                if node_type == "root":
                    cluster = obj.contract.name
            
            self.nodes[node_id] = {
                "label": label, 
                "type": node_type, 
                "obj": obj, 
                "classes": classes,
                "tooltip": tooltip,
                "cluster": cluster
            }

    def _collect_edges(self, func):
        edges = [] # List of (dst_id, dst_label, kind, dst_obj)
        
        # 0. Modifiers
        modifier_names = set()
        if hasattr(func, 'modifiers'):
            for m in func.modifiers:
                edges.append((m.canonical_name, m.canonical_name, "modifier", m))
                modifier_names.add(m.canonical_name)

        # 1. Internal calls
        for ic in func.internal_calls:
            if isinstance(ic, (Function, Modifier)):
                if ic.canonical_name in modifier_names:
                    continue
                edges.append((ic.canonical_name, ic.canonical_name, "internal", ic))
            elif hasattr(ic, 'function') and ic.function:
                 f = ic.function
                 if hasattr(f, 'canonical_name'):
                     if f.canonical_name in modifier_names:
                         continue
                     edges.append((f.canonical_name, f.canonical_name, "internal", f))
                 else:
                     # Solidity builtin in internal_calls
                     edges.append((str(f), str(f), "solidity", None))

        # 2. Solidity calls
        for sc in func.solidity_calls:
            f = sc.function
            label = str(f)
            edges.append((label, label, "solidity", None))

        # Phase 2: --include-events
        if self.config.include_events:
            for node in func.nodes:
                for op in node.irs:
                    if isinstance(op, EventCall):
                        label = f"emit {op.name}"
                        edges.append((label, label, "event", None))

        # 3. High level calls
        for hlc in func.high_level_calls:
            if isinstance(hlc, tuple):
                contract, op = hlc
                if hasattr(op, 'function') and op.function:
                    f = op.function
                    if hasattr(f, 'canonical_name'):
                        edges.append((f.canonical_name, f.canonical_name, "high_level", f))
                    else:
                        edges.append((f"{contract.name}.{op}", f"{contract.name}.{op}", "high_level", None))
                else:
                    edges.append((f"{contract.name}.{op}", f"{contract.name}.{op}", "high_level", None))

        # 4. Library calls
        for lc in func.library_calls:
            f = lc.function
            if hasattr(f, 'canonical_name'):
                # Note: Slither might not distinguish using-for here easily without deeper IR analysis
                edges.append((f.canonical_name, f.canonical_name, "library", f))

        # 5. Low level calls
        for llc in func.low_level_calls:
            label = str(llc)
            edges.append((label, label, "low_level", None))

        # Phase 2: --include-overrides
        if self.config.include_overrides and hasattr(func, 'overrides'):
            for o in func.overrides:
                edges.append((o.canonical_name, o.canonical_name, "override", o))

        # Deduplicate and prioritize
        deduped = self._deduplicate_edges(edges)
        
        # Phase 2: Apply Display Filters
        filtered = []
        for dst_id, label, kind, obj in deduped:
            if self.config.no_errors and (label.startswith("revert") or kind == "error"):
                continue
            if self.config.no_builtins:
                if kind == "solidity" and not label.startswith("revert"):
                    continue
            filtered.append((dst_id, label, kind, obj))
            
        return filtered

    def _deduplicate_edges(self, edges):
        # Priority: low_level > library > high_level > internal > solidity > modifier > event > override
        priority = {
            "low_level": 0,
            "library": 1,
            "high_level": 2,
            "internal": 3,
            "solidity": 4,
            "modifier": 5,
            "event": 6,
            "override": 7
        }
        
        best_edges = {} # dst_id -> (dst_label, kind, dst_obj)
        for dst_id, dst_label, kind, dst_obj in edges:
            if dst_id not in best_edges:
                best_edges[dst_id] = (dst_label, kind, dst_obj)
            else:
                current_kind = best_edges[dst_id][1]
                if priority[kind] < priority[current_kind]:
                    best_edges[dst_id] = (dst_label, kind, dst_obj)
        
        return [(dst_id, label, kind, obj) for dst_id, (label, kind, obj) in best_edges.items()]
