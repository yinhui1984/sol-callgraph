from sol_callgraph.dot import escape_dot_id, DotRenderer, format_node

def test_escape_dot_id():
    assert escape_dot_id('normal') == '"normal"'
    assert escape_dot_id('with "quotes"') == '"with \\"quotes\\""'
    assert escape_dot_id('with \\backslash') == '"with \\\\backslash"'
    assert escape_dot_id('with\nnewline') == '"with\\nnewline"'
    assert escape_dot_id('complex "string" with \\ and \n') == '"complex \\"string\\" with \\\\ and \\n"'

def test_dot_renderer_basic():
    renderer = DotRenderer()
    renderer.add_node("A", label="Node A")
    renderer.add_node("B", label="Node B", style="dashed")
    renderer.add_edge("A", "B", label="calls")
    
    dot_output = renderer.render()
    assert 'digraph focused_call_graph {' in dot_output
    assert 'rankdir="LR";' in dot_output
    assert '  "A" [style="rounded", label="Node A"];' in dot_output
    assert '  "B" [style="dashed", label="Node B"];' in dot_output
    assert '  "A" -> "B" [label="calls"];' in dot_output

def test_dot_renderer_global_attributes():
    renderer = DotRenderer(
        graph_attrs={"nodesep": "0.8", "ranksep": "1.2", "pad": "0.5"},
        node_attrs={"margin": "0.6,0.1", "fontsize": "14", "fontname": "Courier"},
    )
    dot_output = renderer.render()

    assert '  nodesep="0.8";' in dot_output
    assert '  ranksep="1.2";' in dot_output
    assert '  pad="0.5";' in dot_output
    assert 'node [shape="box", style="rounded", fontname="Courier", margin="0.6,0.1", fontsize="14"]' in dot_output

def test_format_node():
    renderer = DotRenderer()
    format_node(renderer, "root_fn", "_fallback()", "root", tooltip="root tooltip")
    format_node(renderer, "ext_fn", "Lib.call()", "expandable", tooltip="ext tooltip")
    format_node(renderer, "builtin_fn", "abi.decode()", "builtin-like", tooltip="builtin tooltip")
    format_node(renderer, "unresolved_fn", "unknown()", "unresolved", tooltip="unresolved tooltip")
    
    dot_output = renderer.render()
    assert '  "root_fn" [style="rounded", label="_fallback()", class="root function", tooltip="root tooltip"];' in dot_output
    assert '  "ext_fn" [style="rounded,dashed", label="Lib.call()", class="expandable function", tooltip="ext tooltip"];' in dot_output
    assert '  "builtin_fn" [style="rounded,dotted", label="abi.decode()", class="builtin-like function", color="gray", fontcolor="gray", tooltip="builtin tooltip"];' in dot_output
    assert '  "unresolved_fn" [style="rounded,dashed", label="unknown()", class="unresolved function", color="gray", fontcolor="gray", tooltip="unresolved tooltip"];' in dot_output
