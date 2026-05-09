import json

def escape_dot_id(id_str: str) -> str:
    """Escapes a string for use as a DOT ID or label."""
    # Simple JSON dumps can handle many escapes, but DOT has its own rules.
    # For DOT, we just need to escape double quotes and backslashes, and handle newlines.
    escaped = id_str.replace('\\', '\\\\').replace('"', '\\"').replace('\n', '\\n')
    return f'"{escaped}"'

class DotRenderer:
    def __init__(self, name: str = "focused_call_graph"):
        self.name = name
        self.nodes = []
        self.edges = []
        self.clusters = {} # name -> {label, nodes}
        self.rankdir = "LR"

    def add_node(self, name: str, label: str = None, style: str = "rounded", 
                 class_attr: str = None, color: str = None, tooltip: str = None,
                 cluster: str = None):
        attrs = [f'style={escape_dot_id(style)}']
        if label:
            attrs.append(f'label={escape_dot_id(label)}')
        if class_attr:
            attrs.append(f'class={escape_dot_id(class_attr)}')
        if color:
            attrs.append(f'color={escape_dot_id(color)}')
            attrs.append(f'fontcolor={escape_dot_id(color)}')
        if tooltip:
            attrs.append(f'tooltip={escape_dot_id(tooltip)}')
        
        attr_str = ", ".join(attrs)
        node_line = f'  {escape_dot_id(name)} [{attr_str}];'
        
        if cluster:
            if cluster not in self.clusters:
                self.clusters[cluster] = {"label": cluster, "nodes": []}
            self.clusters[cluster]["nodes"].append(node_line)
        else:
            self.nodes.append(node_line)

    def add_edge(self, src: str, dst: str, label: str = None, 
                 class_attr: str = None, tooltip: str = None, 
                 style: str = None, constraint: bool = True):
        attrs = []
        if label:
            attrs.append(f'label={escape_dot_id(label)}')
        if class_attr:
            attrs.append(f'class={escape_dot_id(class_attr)}')
        if tooltip:
            attrs.append(f'tooltip={escape_dot_id(tooltip)}')
        if style:
            attrs.append(f'style={escape_dot_id(style)}')
        if not constraint:
            attrs.append('constraint=false')
        
        attr_str = ""
        if attrs:
            attr_str = f' [{", ".join(attrs)}]'
        
        self.edges.append(f'  {escape_dot_id(src)} -> {escape_dot_id(dst)}{attr_str};')

    def render(self) -> str:
        lines = [
            f'digraph {self.name} {{',
            f'  rankdir={escape_dot_id(self.rankdir)};',
            '  node [shape=box, style="rounded", fontname="Helvetica"];',
            '  edge [fontname="Helvetica"];',
            ''
        ]
        
        # Add clusters
        for c_name, data in self.clusters.items():
            # Standard Graphviz cluster prefix
            cluster_id = f"cluster_{c_name.replace('.', '_').replace('(', '_').replace(')', '_')}"
            lines.append(f'  subgraph {escape_dot_id(cluster_id)} {{')
            lines.append(f'    label={escape_dot_id(data["label"])};')
            lines.append('    style="filled,rounded";')
            lines.append('    color="#f0f0f0";')
            for node_line in data["nodes"]:
                lines.append(f'  {node_line}')
            lines.append('  }')
            
        lines.extend(self.nodes)
        if (self.nodes or self.clusters) and self.edges:
            lines.append('')
        lines.extend(self.edges)
        lines.append('}')
        return '\n'.join(lines)

def format_node(renderer: DotRenderer, node_id: str, label: str, node_type: str, 
                classes: str = None, tooltip: str = None, cluster: str = None):
    """
    Applies styling based on node type:
    - root: solid rounded box
    - expandable: rounded dashed box
    - builtin-like: rounded dotted gray box
    - error-like: rounded dotted gray box (different class)
    - event-like: rounded dotted gray box (different class)
    - unresolved: rounded dashed gray box
    """
    if classes is None:
        classes = f"{node_type} function"
        
    if node_type == "root":
        renderer.add_node(node_id, label=label, style="rounded", class_attr=classes, 
                          tooltip=tooltip, cluster=cluster)
    elif node_type == "expandable":
        renderer.add_node(node_id, label=label, style="rounded,dashed", class_attr=classes, 
                          tooltip=tooltip, cluster=cluster)
    elif node_type in ("builtin-like", "error-like", "event-like"):
        renderer.add_node(node_id, label=label, style="rounded,dotted", class_attr=classes, 
                          color="gray", tooltip=tooltip, cluster=cluster)
    elif node_type == "unresolved":
        renderer.add_node(node_id, label=label, style="rounded,dashed", class_attr=classes, 
                          color="gray", tooltip=tooltip, cluster=cluster)
    else:
        renderer.add_node(node_id, label=label, style="rounded", class_attr=classes, 
                          tooltip=tooltip, cluster=cluster)
