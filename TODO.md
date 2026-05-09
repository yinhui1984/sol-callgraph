# sol-callgraph TODO

本文档记录当前实现状态和后续未实现功能。

第一阶段详细设计见：

```text
docs/sol-callgraph_requirements_design.md
```

第二阶段详细设计见：

```text
docs/sol-callgraph_phase2_requirements.md
```

## v0.1 已完成并已测试

### 核心功能

- [x] 默认以目标文件为 root scope，且 root 只包含目标文件/目标声明中 declared 且有实现的函数与 modifier。
- [x] 继承函数不再误标为 root；继承函数可作为 expandable 外部节点出现。
- [x] 支持通过 `--contract` 指定特定 contract/library/interface 声明作为 root。
- [x] `--contract` 找不到目标声明时返回 exit 3，并列出 available declarations。
- [x] 默认输出标准 DOT 到 stdout。
- [x] 诊断、warning 和日志输出到 stderr。
- [x] 支持 `--quiet` 抑制非必要 warning。
- [x] 支持 `--verbose` 输出基础诊断信息。
- [x] 收集 Slither 识别的调用类型：internal、solidity、high_level、library、low_level。
- [x] 支持同一 `(src, dst)` 的边去重和优先级选择。
- [x] 支持外部可解析函数作为 expandable 节点。
- [x] 支持 `--depth` 的受限 BFS 展开模型。
- [x] 支持节点分类：root、expandable、builtin-like、unresolved。
- [x] 支持 DOT 字符串与 ID 转义。
- [x] 支持 `--format dot|svg|png`。
- [x] SVG/PNG 输出只在需要时依赖 Graphviz。
- [x] 修复 SVG/PNG stdout 模式重复调用 Graphviz 的问题。
- [x] 支持 `--list-contracts`。
- [x] 支持 modifier 边，edge label 为 `modifier`。
- [x] 支持多声明文件默认 file scope，并输出 warning。
- [x] 支持 Slither Python 自动探测。
- [x] 支持 `--debug-env`。
- [x] 支持 `--slither-python` 作为 launcher 参数。
- [x] 提供根目录包装脚本 `./sol-callgraph`。

### 测试与验证

- [x] 单元测试：DOT 渲染逻辑。
- [x] 单元测试：OpenZeppelin selftest 分类逻辑。
- [x] 集成测试：基础内部调用。
- [x] 集成测试：modifier 边。
- [x] 集成测试：继承函数不作为 root。
- [x] OpenZeppelin smoke test。
- [x] OpenZeppelin selftest。
- [x] OpenZeppelin 固定核心样本 PASS。
- [x] TransparentUpgradeableProxy 关键边断言 PASS。
- [x] 自动样本发现，默认最多 30 个。
- [x] interface-only 样本按 `EXPECTED_NO_ROOT` 处理，不计入 FAIL。
- [x] 存在真实失败时 selftest 返回非 0。
- [x] 自测报告包含 Slither version、OpenZeppelin commit、节点/边统计和分类汇总。
- [x] `failures.json` 只记录真实失败。
- [x] Makefile 封装：`make test-all`。

## Phase 2 未实现功能总览

以下清单来自 `docs/sol-callgraph_phase2_requirements.md` 和早期设计建议。没有实现没关系，但不能漏登记。

### A. Project root 与编译上下文

- [ ] 自动 project root 检测，优先识别 Solidity 编译框架 marker。
- [ ] 强 marker：`foundry.toml`、`hardhat.config.*`、`truffle-config.js`、`truffle.js`、`brownie-config.yaml`、`ape-config.yaml`、`dapp.json`。
- [ ] 弱 marker：`remappings.txt`、`package.json`、`.git`。
- [ ] `--root <dir>`：显式指定 Slither cwd / Solidity project root。
- [ ] `--no-root-detect`：禁用自动 root 检测。
- [ ] `--print-env`：输出 target、detected root、root reason、slither cwd、slither target、slither binary、slither python。
- [ ] target 在 root 内时，传相对 root 的路径给 Slither。
- [ ] Foundry-like project fixture。
- [ ] monorepo nested `foundry.toml` fixture。
- [ ] standalone file outside project marker fixture。

### B. Scope 与 root 控制

- [ ] `--include-inherited`：把继承来的可见函数/modifier 也作为 root。
- [ ] inherited root 节点通过 class/tooltip 标记 inherited。
- [ ] `--include-interfaces`：允许 interface 函数作为 root leaf 节点出现。
- [ ] `--no-constructors`：隐藏 constructor root。
- [ ] `--root-function <canonical-or-unique-name>`：只从指定函数开始绘图，可重复。
- [ ] `--root-function` 支持完整 canonical name。
- [ ] `--root-function` 短名只在唯一匹配时接受。
- [ ] 函数重载导致歧义时返回错误并列出候选。

### C. 显示控制

- [ ] `--include-events`：显示 event emit leaf，edge label 为 `event`。
- [ ] `--include-errors` / `--no-errors`：控制 custom error / revert leaf。
- [ ] `--include-builtins` / `--no-builtins`：控制 abi.decode / require / assert / keccak256 等 builtin leaf。
- [ ] 保持默认图不因新增 include/exclude 参数意外变化。

### D. 语义边与非执行边

- [ ] 区分 resolved edge、symbolic edge、builtin edge、event/error edge、modifier edge、override edge。
- [ ] 文档和 metadata 明确 modifier edge 不表示普通函数调用顺序。
- [ ] `--include-overrides`：显示 override / overrides 关系。
- [ ] override 边必须标记为 semantic / non-execution edge。
- [ ] low-level call / delegatecall / staticcall 明确标记为 symbolic edge。
- [ ] external/high-level/interface call metadata：static target type、runtime target expression、function signature。
- [ ] using-for library call metadata。
- [ ] using-for fixture，例如 `using SafeERC20 for IERC20; token.safeTransfer(...)`。

### E. Initializer、entrypoint 与节点语义

- [ ] `--detect-initializers`。
- [ ] `--profile upgradeable`，可等价启用 initializer 识别。
- [ ] 识别 initializer / reinitializer / onlyInitializing modifier。
- [ ] 识别 `initialize`、`__*_init`、`__*_init_unchained`。
- [ ] 给 initializer 相关节点加 class 或 tooltip。
- [ ] entrypoint metadata：external/public function、constructor、fallback、receive、initializer。
- [ ] fallback / receive 节点标记为 entrypoint。

### F. 稳定 Node ID 与 DOT/SVG metadata

- [ ] 使用更稳定的内部节点 ID：`source_unit::contract::function_signature`。
- [ ] 避免不同文件同名 contract/function 的节点 ID 冲突。
- [ ] 节点 metadata：label、class、tooltip、URL 或 id、source path、declaration kind、function kind、visibility、role。
- [ ] 边 metadata：label、class、tooltip、semantic kind、resolved/symbolic。
- [ ] SVG 输出保留可供未来 reader 使用的语义属性。
- [ ] 增强 SVG 输出：URL、tooltip、CSS class。

### G. Cluster 与布局控制

- [ ] `--cluster`：按 root declaration 分 cluster。
- [ ] `--no-cluster`：关闭 cluster。
- [ ] cluster 只包含 root declarations。
- [ ] external expandable / builtin / event / error 节点默认不放入 cluster。

### H. 图规模保护与诊断

- [ ] `--max-nodes <n>`。
- [ ] `--max-edges <n>`。
- [ ] 达到节点/边上限时输出 warning，并标记图可能被截断。
- [ ] `--max-nodes 0` / `--max-edges 0` 表示禁用限制。
- [ ] verbose 模式输出 unresolved call 分类统计。
- [ ] `--fail-on-unresolved`。
- [ ] `--fail-on-warning`。

### I. Slither / solc 参数与调试

- [ ] `--slither-arg <arg>`，可重复透传给 Slither 初始化/编译层。
- [ ] `--solc-remaps <value>`。
- [ ] `--solc-args <value>`。
- [ ] `--compile-force-framework <foundry|hardhat|brownie|truffle>`。
- [ ] `--debug-slither`：显示完整 Slither 调用环境、cwd、target、Slither Python、root reason、透传参数。
- [ ] 不吞掉 Slither/solc warning。
- [ ] `--quiet` 只抑制 warning/info，不抑制 error。

### J. JSON 与机器消费

- [ ] `--format json`。
- [ ] JSON 包含 schema_version、target、project_root、root_scope、nodes、edges、warnings、stats、tool_version、slither_version。
- [ ] JSON node 包含 id、label、kind、role、source、contract、signature、visibility、classes、tooltip。
- [ ] JSON edge 包含 src、dst、kind、resolved、classes、tooltip。
- [ ] JSON stdout 必须保持纯净。

### K. Cache 策略

- [ ] 暂不默认启用缓存。
- [ ] 如果实现缓存，cache key 必须包含 target path、target hash/mtime、project root、config/remappings hash、sol-callgraph version、Slither version、depth、contract filters、root-function filters、include flags、format。

### L. Stdin 行为

- [ ] 明确拒绝 stdin 输入：`sol-callgraph -`。
- [ ] 错误说明：工具需要真实文件路径用于 Slither/import resolution。

### M. 测试矩阵扩展

- [ ] 多文件/多项目 fixture 矩阵，不只依赖 OpenZeppelin。
- [ ] single file, one contract。
- [ ] single file, contract + interface + library。
- [ ] multiple contracts with same function names。
- [ ] function overload。
- [ ] constructor calling parent constructor。
- [ ] fallback / receive。
- [ ] low-level call。
- [ ] delegatecall。
- [ ] staticcall。
- [ ] using-for library。
- [ ] custom error revert。
- [ ] event emit。
- [ ] interface call。
- [ ] inheritance override。
- [ ] abstract contract。
- [ ] proxy-like dynamic implementation。
- [ ] file outside git/project。
- [ ] Foundry-like project。
- [ ] monorepo nested foundry.toml。
- [ ] package.json fallback。

### N. README / CLI help / 用户文档

- [ ] README 从极简说明升级为可用文档。
- [ ] README 说明安装与 `.venv` 开发环境。
- [ ] README 说明 project root 行为。
- [ ] README 说明 scope 控制。
- [ ] README 说明 depth 模型。
- [ ] README 说明输出格式。
- [ ] README 说明 OpenZeppelin selftest。
- [ ] README 说明常见错误。
- [ ] README 明确不承诺项：不是 execution graph、不是攻击路径搜索器、不是链上状态解析器。
- [ ] CLI help 列出所有真实支持的参数。
- [ ] launcher-only 参数不只藏在 description 中。

## Phase 2 建议实施顺序

建议按以下顺序实施，不要一次性全做：

1. Project root 检测：`--root` / `--no-root-detect` / `--print-env`。
2. README 和 CLI help 更新。
3. Scope 控制：`--include-inherited` / `--include-interfaces` / `--root-function`。
4. 显示控制：`--no-builtins` / `--no-errors` / `--include-events` / `--no-constructors`。
5. 语义 metadata：entrypoint、initializer、external call、using-for。
6. Override 边：`--include-overrides`。
7. 稳定 node id 和 DOT metadata。
8. Cluster：`--cluster` / `--no-cluster`。
9. 图规模保护和 unresolved 统计。
10. Slither 参数透传和 `--debug-slither`。
11. JSON 输出。
12. 扩展 fixture 矩阵和 OpenZeppelin selftest。

每一步都必须保持：

```bash
./.venv/bin/python -m pytest
./.venv/bin/python -m sol_callgraph.selftest_openzeppelin
make test-all
```

通过，或明确记录失败原因。
