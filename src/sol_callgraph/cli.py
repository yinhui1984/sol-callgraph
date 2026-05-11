import argparse
import sys
import locale
import shlex
from typing import Dict, List, Optional

def get_lang():
    try:
        lang, _ = locale.getlocale()
        if lang and lang.startswith('zh'):
            return 'zh'
    except:
        pass
    return 'en'

LANG = get_lang()

I18N = {
    'en': {
        'description': (
            "sol-callgraph: A focused call graph exporter for Solidity.\n\n"
            "This tool generates concise call graphs centered around a specific Solidity file or contract.\n"
            "Unlike standard Slither printers, it ensures that critical calls across files, libraries, \n"
            "and proxies (like ERC1967) are retained while filtering out project-wide noise.\n\n"
            "Environment Management:\n"
            "  --debug-env              (Launcher only) Print Slither environment info and exit\n"
            "  --slither-python <path>  (Launcher only) Explicitly set the Python interpreter with Slither installed\n"
            "  --print-env              Print compilation environment info and exit"
        ),
        'error': 'error',
        'target_help': 'Target Solidity file',
        'contract_help': 'Focus on specific contract/library/interface (can be repeated)',
        'depth_help': 'Depth of call graph expansion (default: 1)',
        'out_help': 'Output file path (default: stdout)',
        'format_help': 'Output format (default: dot)',
        'list_contracts_help': 'List all recognized contracts/libraries in the target file and exit',
        'quiet_help': 'Suppress non-essential warnings',
        'verbose_help': 'Enable detailed diagnostic logging',
        'root_help': 'Explicitly specify the Solidity project root directory',
        'no_root_detect_help': 'Disable automatic project root detection',
        'print_env_help': 'Print detected compilation environment and exit',
        'include_inherited_help': 'Include inherited functions/modifiers in the root scope',
        'include_interfaces_help': 'Include interface functions as root nodes',
        'root_function_help': 'Start the call graph from specific function names (can be repeated)',
        'include_events_help': 'Include event emissions in the graph',
        'no_errors_help': 'Hide custom error and revert nodes',
        'no_builtins_help': 'Hide Solidity built-in functions (e.g., abi.decode, keccak256)',
        'no_constructors_help': 'Exclude constructor functions from the root scope',
        'include_overrides_help': 'Include override/overrides relationships in the graph',
        'cluster_help': 'Cluster functions by contract',
        'no_cluster_help': 'Disable clustering (default)',
        'max_nodes_help': 'Maximum number of nodes in the graph (default: 500, 0 for unlimited)',
        'max_edges_help': 'Maximum number of edges in the graph (default: 1000, 0 for unlimited)',
        'fail_on_unresolved_help': 'Exit with non-zero code if there are unresolved calls',
        'fail_on_warning_help': 'Exit with non-zero code if there are warnings',
        'slither_arg_help': 'Pass Slither kwargs or graph/node/edge attributes (repeat; quote values with spaces)',
        'solc_remaps_help': 'Pass remappings to solc',
        'solc_args_help': 'Pass extra arguments to solc',
        'compile_force_framework_help': 'Force Slither to use a specific compilation framework',
        'debug_slither_help': 'Show detailed Slither invocation and environment info',
        'err_no_target': 'no target file specified',
        'err_stdin': "stdin input '-' is not supported. sol-callgraph requires a real file path for Slither analysis.",
        'err_depth': '--depth must be >= 1',
    },
    'zh': {
        'description': (
            "sol-callgraph: 针对 Solidity 的聚焦调用图导出工具。\n\n"
            "该工具生成以特定 Solidity 文件或合约为中心的简洁调用图。\n"
            "与标准的 Slither 打印器不同，它确保保留跨文件、库和代理（如 ERC1967）的关键调用，\n"
            "同时过滤掉项目范围内的噪音。\n\n"
            "环境管理：\n"
            "  --debug-env              (仅限 Launcher) 打印 Slither 环境信息并退出\n"
            "  --slither-python <path>  (仅限 Launcher) 显式设置安装了 Slither 的 Python 解释器\n"
            "  --print-env              打印检测到的编译环境信息并退出"
        ),
        'error': '错误',
        'target_help': '目标 Solidity 文件',
        'contract_help': '聚焦于特定的合约/库/接口（可重复）',
        'depth_help': '调用图展开深度（默认：1）',
        'out_help': '输出文件路径（默认：stdout）',
        'format_help': '输出格式（默认：dot）',
        'list_contracts_help': '列出目标文件中所有识别到的合约/库并退出',
        'quiet_help': '抑制非必要的警告',
        'verbose_help': '启用详细的诊断日志',
        'root_help': '显式指定 Solidity 项目根目录',
        'no_root_detect_help': '禁用自动项目根目录检测',
        'print_env_help': '打印检测到的编译环境并退出',
        'include_inherited_help': '在根作用域中包含继承的函数/修改器',
        'include_interfaces_help': '将接口函数作为根节点包含',
        'root_function_help': '从特定的函数名开始生成调用图（可重复）',
        'include_events_help': '在图中包含事件触发',
        'no_errors_help': '隐藏自定义错误和 revert 节点',
        'no_builtins_help': '隐藏 Solidity 内置函数（如 abi.decode, keccak256）',
        'no_constructors_help': '从根作用域中排除构造函数',
        'include_overrides_help': '在图中包含 override/overrides 关系',
        'cluster_help': '按合约对函数进行分组（Cluster）',
        'no_cluster_help': '禁用分组（默认）',
        'max_nodes_help': '图中的最大节点数（默认：500，0 表示不限制）',
        'max_edges_help': '图中的最大边数（默认：1000，0 表示不限制）',
        'fail_on_unresolved_help': '如果存在未解析的调用，以非零代码退出',
        'fail_on_warning_help': '如果存在警告，以非零代码退出',
        'slither_arg_help': '传递 Slither kwargs 或 graph/node/edge 属性（可重复；含空格需加引号）',
        'solc_remaps_help': '向 solc 传递重映射（Remappings）',
        'solc_args_help': '向 solc 传递额外参数',
        'compile_force_framework_help': '强制 Slither 使用特定的编译框架',
        'debug_slither_help': '显示详细的 Slither 调用信息和环境信息',
        'err_no_target': '未指定目标文件',
        'err_stdin': "不支持标准输入 '-'。sol-callgraph 需要真实的文件路径进行 Slither 分析。",
        'err_depth': '--depth 必须 >= 1',
    }
}

T = I18N[LANG]

def _parse_attribute_list(value: str) -> Dict[str, str]:
    attrs = {}
    for token in shlex.split(value):
        if "=" not in token:
            raise ValueError(f"expected KEY=VALUE attribute, got {token!r}")
        key, attr_value = token.split("=", 1)
        if not key:
            raise ValueError(f"empty attribute name in {token!r}")
        attrs[key] = attr_value
    return attrs

def parse_slither_args(values: List[str]):
    slither_kwargs = {}
    graph_attrs = {}
    node_attrs = {}
    edge_attrs = {}
    i = 0
    while i < len(values):
        value = values[i]
        if value in ("--graph-attributes", "--node-attributes", "--edge-attributes"):
            if i + 1 >= len(values):
                raise ValueError(f"{value} requires a following --slither-arg=KEY=VALUE list")
            try:
                attrs = _parse_attribute_list(values[i + 1])
            except ValueError as e:
                raise ValueError(f"{value}: {e}") from e
            if value == "--graph-attributes":
                graph_attrs.update(attrs)
            elif value == "--node-attributes":
                node_attrs.update(attrs)
            else:
                edge_attrs.update(attrs)
            i += 2
            continue

        if value.startswith("--"):
            raise ValueError(
                f"unsupported Slither CLI flag {value!r}; use KEY=VALUE for Slither Python kwargs"
            )
        if "=" not in value:
            raise ValueError(f"expected KEY=VALUE slither argument, got {value!r}")
        key, arg_value = value.split("=", 1)
        if not key:
            raise ValueError(f"empty slither argument name in {value!r}")
        slither_kwargs[key.replace("-", "_")] = arg_value
        i += 1
    return slither_kwargs, graph_attrs, node_attrs, edge_attrs

class CustomHelpFormatter(argparse.RawDescriptionHelpFormatter):
    def __init__(self, prog):
        # Increase max_help_position to give more room for option strings
        super().__init__(prog, max_help_position=45)

class SmartArgumentParser(argparse.ArgumentParser):
    def error(self, message):
        sys.stderr.write(f'{T["error"]}: {message}\n\n')
        self.print_help()
        sys.exit(1)

class Config:
    def __init__(self, args: argparse.Namespace, parser: SmartArgumentParser):
        self.target = args.target
        self.contracts = args.contract or []
        self.depth = args.depth
        self.out = args.out
        self.format = args.format
        self.list_contracts = args.list_contracts
        self.quiet = args.quiet
        self.verbose = args.verbose
        self.parser = parser
        # Phase 2
        self.root = args.root
        self.no_root_detect = args.no_root_detect
        self.print_env = args.print_env
        self.include_inherited = args.include_inherited
        self.include_interfaces = args.include_interfaces
        self.root_function = args.root_function or []
        # Phase 2 Display Controls
        self.include_events = args.include_events
        self.no_errors = args.no_errors
        self.no_builtins = args.no_builtins
        self.no_constructors = args.no_constructors
        self.include_overrides = args.include_overrides
        self.cluster = args.cluster
        # Phase 2 Size Protection & Diagnostics
        self.max_nodes = args.max_nodes
        self.max_edges = args.max_edges
        self.fail_on_unresolved = args.fail_on_unresolved
        self.fail_on_warning = args.fail_on_warning
        # Phase 2 Slither/solc passthrough
        self.slither_args = args.slither_arg or []
        try:
            (
                self.slither_kwargs,
                self.graph_attributes,
                self.node_attributes,
                self.edge_attributes,
            ) = parse_slither_args(self.slither_args)
        except ValueError as e:
            parser.error(str(e))
        self.solc_remaps = args.solc_remaps
        self.solc_args = args.solc_args
        self.compile_force_framework = args.compile_force_framework
        self.debug_slither = args.debug_slither

def parse_args(args: List[str]) -> Config:
    parser = SmartArgumentParser(
        prog="sol-callgraph",
        description=T['description'],
        formatter_class=CustomHelpFormatter
    )
    
    # Positionals
    parser.add_argument(
        "target",
        nargs="?",
        help=T['target_help'],
        metavar="TARGET"
    )
    
    # Options
    parser.add_argument(
        "-c", "--contract",
        action="append",
        help=T['contract_help'],
        metavar="NAME"
    )
    parser.add_argument(
        "--depth",
        type=int,
        default=1,
        help=T['depth_help'],
        metavar="N"
    )
    parser.add_argument(
        "-o", "--out",
        help=T['out_help'],
        metavar="PATH"
    )
    parser.add_argument(
        "--format",
        choices=["dot", "svg", "png", "json"],
        default="dot",
        help=T['format_help']
    )
    parser.add_argument(
        "--list-contracts",
        action="store_true",
        help=T['list_contracts_help']
    )
    parser.add_argument(
        "--quiet",
        action="store_true",
        help=T['quiet_help']
    )
    parser.add_argument(
        "-v", "--verbose",
        action="store_true",
        help=T['verbose_help']
    )
    
    # Phase 2 Options
    parser.add_argument(
        "--root",
        help=T['root_help'],
        metavar="PATH"
    )
    parser.add_argument(
        "--no-root-detect",
        action="store_true",
        help=T['no_root_detect_help']
    )
    parser.add_argument(
        "--print-env",
        action="store_true",
        help=T['print_env_help']
    )
    parser.add_argument(
        "--include-inherited",
        action="store_true",
        help=T['include_inherited_help']
    )
    parser.add_argument(
        "--include-interfaces",
        action="store_true",
        help=T['include_interfaces_help']
    )
    parser.add_argument(
        "--root-function",
        action="append",
        help=T['root_function_help'],
        metavar="FUNC"
    )
    
    parser.add_argument(
        "--include-events",
        action="store_true",
        help=T['include_events_help']
    )
    parser.add_argument(
        "--no-errors",
        action="store_true",
        help=T['no_errors_help']
    )
    parser.add_argument(
        "--no-builtins",
        action="store_true",
        help=T['no_builtins_help']
    )
    parser.add_argument(
        "--no-constructors",
        action="store_true",
        help=T['no_constructors_help']
    )
    parser.add_argument(
        "--include-overrides",
        action="store_true",
        help=T['include_overrides_help']
    )
    
    parser.add_argument(
        "--cluster",
        action="store_true",
        default=False,
        help=T['cluster_help']
    )
    parser.add_argument(
        "--no-cluster",
        action="store_false",
        dest="cluster",
        help=T['no_cluster_help']
    )
    
    parser.add_argument(
        "--max-nodes",
        type=int,
        default=500,
        help=T['max_nodes_help'],
        metavar="N"
    )
    parser.add_argument(
        "--max-edges",
        type=int,
        default=1000,
        help=T['max_edges_help'],
        metavar="N"
    )
    parser.add_argument(
        "--fail-on-unresolved",
        action="store_true",
        help=T['fail_on_unresolved_help']
    )
    parser.add_argument(
        "--fail-on-warning",
        action="store_true",
        help=T['fail_on_warning_help']
    )
    
    # Phase 2 Slither/solc passthrough
    parser.add_argument(
        "--slither-arg",
        action="append",
        help=T['slither_arg_help'],
        metavar="ARG"
    )
    parser.add_argument(
        "--solc-remaps",
        help=T['solc_remaps_help'],
        metavar="REMAPS"
    )
    parser.add_argument(
        "--solc-args",
        help=T['solc_args_help'],
        metavar="ARGS"
    )
    parser.add_argument(
        "--compile-force-framework",
        choices=["foundry", "hardhat", "truffle", "brownie", "ape"],
        help=T['compile_force_framework_help'],
        metavar="FRAMEWORK"
    )
    parser.add_argument(
        "--debug-slither",
        action="store_true",
        help=T['debug_slither_help']
    )

    parsed_args = parser.parse_args(args)

    if parsed_args.target == "-":
        sys.stderr.write(f'{T["error"]}: {T["err_stdin"]}\n\n')
        parser.print_help()
        sys.exit(1)

    if parsed_args.depth < 1:
        sys.stderr.write(f'{T["error"]}: {T["err_depth"]}\n\n')
        parser.print_help()
        sys.exit(1)
        
    return Config(parsed_args, parser)
