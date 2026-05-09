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

## v0.2 Phase 2 当前完成状态

### A. Project root 与编译上下文

- [x] 自动 project root 检测，优先识别 Solidity 编译框架 marker。
- [x] 强 marker：`foundry.toml`、`hardhat.config.*`、`truffle-config.js`、`truffle.js`、`brownie-config.yaml`、`ape-config.yaml`、`dapp.json`。
- [x] 弱 marker：`remappings.txt`、`package.json`、`.git`。
- [x] `--root <dir>`：显式指定 Slither cwd / Solidity project root。
- [x] `--no-root-detect`：禁用自动 root 检测。
- [x] `--print-env`：输出 target、detected root、root reason、slither cwd、slither target、slither binary、slither python。
- [x] target 在 root 内时，传相对 root 的路径给 Slither。
- [x] Foundry-like project fixture。
- [x] standalone file outside project marker fixture。

### B. Scope 与 root 控制

- [x] `--include-inherited`：把继承来的可见函数/modifier 也作为 root。
- [x] inherited root 节点通过 class/tooltip 标记 inherited。
- [x] `--include-interfaces`：允许 interface 函数作为 root leaf 节点出现。
- [x] `--no-constructors`：隐藏 constructor root。
- [x] `--root-function <canonical-or-unique-name>`：只从指定函数开始绘图，可重复。
- [x] `--root-function` 支持完整 canonical name。
- [x] `--root-function` 短名只在 unique 匹配时接受。
- [x] 函数重载导致歧义时返回错误并列出候选。

### C. 显示控制

- [x] `--include-events`：显示 event emit leaf，edge label 为 `event`。
- [x] `--include-errors` / `--no-errors`：控制 custom error / revert leaf。
- [x] `--include-builtins` / `--no-builtins`：控制 abi.decode / require / assert / keccak256 等 builtin leaf。
- [x] 保持默认图不因新增 include/exclude 参数意外变化。

### D. 语义边与非执行边

- [x] 区分 resolved edge、symbolic edge、builtin edge、event/error edge、modifier edge、override edge。
- [x] 文档和 metadata 明确 modifier edge 不表示普通函数调用顺序。
- [x] `--include-overrides`：显示 override / overrides 关系。
- [x] override 边标记为 semantic / non-execution edge (通过 class=edge-override)。
- [ ] low-level call / delegatecall / staticcall 明确标记为 symbolic edge。
- [ ] external/high-level/interface call metadata：static target type、runtime target expression、function signature。
- [x] using-for library call 支持。

### E. Initializer、entrypoint 与节点语义

- [x] `--detect-initializers` (默认通过名称和 modifier 识别)。
- [x] 识别 initializer / reinitializer / onlyInitializing modifier。
- [x] 识别 `initialize`、`__*_init`、`__*_init_unchained`。
- [x] 给 initializer 相关节点加 class 或 tooltip。
- [x] entrypoint metadata：external/public function、constructor、fallback、receive、initializer。
- [x] fallback / receive 节点标记为 entrypoint。

### F. 稳定 Node ID 与 DOT/SVG metadata

- [x] 使用更稳定的内部节点 ID：`source_unit::contract::function_signature`。
- [x] 避免不同文件同名 contract/function 的节点 ID 冲突。
- [x] 节点 metadata：label、class、tooltip、URL 或 id、source path、declaration kind、function kind、visibility、role。
- [x] 边 metadata：label、class、tooltip、semantic kind、resolved/symbolic。
- [x] SVG 输出保留可供未来 reader 使用的语义属性。
- [x] 增强 SVG 输出：URL、tooltip、CSS class。

### G. Cluster 与布局控制

- [x] `--cluster`：按 root declaration 分 cluster。
- [x] `--no-cluster`：关闭 cluster (默认行为)。
- [x] cluster 只包含 root declarations。
- [x] external expandable / builtin / event / error 节点默认不放入 cluster。

### H. 图规模保护与诊断

- [x] `--max-nodes <n>` (默认 500)。
- [x] `--max-edges <n>` (默认 1000)。
- [x] 达到节点/边上限时输出 warning，并标记图可能被截断。
- [x] `--max-nodes 0` / `--max-edges 0` 表示禁用限制。
- [x] verbose 模式输出 unresolved call 分类统计。
- [x] `--fail-on-unresolved`。
- [x] `--fail-on-warning`。

### I. Slither / solc 参数与调试

- [x] `--slither-arg <arg>` (通过 slither_kwargs 透传)。
- [x] `--solc-remaps <value>`。
- [x] `--solc-args <value>`。
- [x] `--compile-force-framework <foundry|hardhat|brownie|truffle|ape>`。
- [x] `--debug-slither`：显示完整 Slither 调用环境、cwd、target、Slither Python、透传参数。
- [x] 不吞掉 Slither/solc warning。
- [x] `--quiet` 只抑制 warning/info，不抑制 error。

### J. JSON 与机器消费

- [x] `--format json`。
- [x] JSON 包含 schema_version、target、project_root、stats、tool_version、slither_version。
- [x] JSON node 包含 id、label、role、classes、tooltip、contract、contract_kind、visibility、signature。
- [x] JSON edge 包含 src、dst, kind, tooltip。
- [x] JSON stdout 保持纯净。

### K. Cache 策略

- [ ] 暂不默认启用缓存。
- [ ] 如果实现缓存，cache key 必须包含 target path、target hash/mtime、project root、config/remappings hash、sol-callgraph version、Slither version、depth、contract filters、root-function filters、include flags、format。

### L. Stdin 行为

- [x] 明确拒绝 stdin 输入：`sol-callgraph -`。
- [x] 错误说明：工具需要真实文件路径用于 Slither/import resolution。

### M. 测试矩阵扩展

- [x] 多文件/多项目 fixture 矩阵，不只依赖 OpenZeppelin。
- [x] single file, one contract.
- [x] single file, contract + interface + library.
- [x] function overload.
- [x] fallback / receive.
- [x] low-level call.
- [x] using-for library.
- [x] custom error revert.
- [x] event emit.
- [x] interface call.
- [x] inheritance override.
- [x] abstract contract.
- [x] file outside git/project.
- [x] Foundry-like project.
- [x] package.json fallback.

### N. README / CLI help / 用户文档

- [x] README 从极简说明升级为可用文档。
- [x] README 说明安装与 `.venv` 开发环境。
- [x] README 说明 project root 行为。
- [x] README 说明 scope 控制。
- [x] README 说明 depth 模型。
- [x] README 说明输出格式。
- [x] README 说明 OpenZeppelin selftest。
- [x] README 说明常见错误。
- [x] README 明确不承诺项：不是 execution graph、不是攻击路径搜索器、不是链上状态解析器。
- [x] CLI help 列出所有真实支持的参数。
- [x] launcher-only 参数不只藏在 description 中。
