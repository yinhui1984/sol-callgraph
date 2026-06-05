# sol-callgraph Phase 2 需求与设计

## 1. 文档目的

本文档定义 `sol-callgraph` 第二阶段要补齐的能力。

第一阶段已经完成 focused DOT 基础功能、Slither Python launcher、depth 展开、modifier 边、OpenZeppelin 自测和基础 SVG/PNG 输出。第二阶段的目标不是推翻第一阶段，而是在现有代码基础上补齐真实项目使用中容易漏掉的功能开关、工程上下文、语义 metadata 和可靠性保护。

本文档不修改第一阶段设计文档。第一阶段文档仍是 v0.1 的验收基线；本文档是后续继续实施的 Phase 2 规格。

## 2. Phase 2 总目标

Phase 2 要解决的问题：

```text
1. 让工具在 Foundry/Hardhat/monorepo 等真实项目中更可靠。
2. 让 root scope、继承、interface、constructor、event、builtin 等显示策略可控。
3. 让图表达更多语义信息，但不伪装成 execution graph。
4. 让大型图有规模保护和可诊断统计。
5. 让输出为未来 reader / SVG 交互 / JSON 消费留出稳定结构。
6. 扩展测试矩阵，避免只靠 OpenZeppelin 这种规整项目。
```

Phase 2 的核心原则：

```text
默认仍保持 focused、保守、可读。
会显著放大图的功能必须显式打开。
新增语义必须通过 edge kind、node class、tooltip 或 metadata 表达清楚。
不要把静态 call graph 伪装成运行时执行路径。
```

## 3. 非目标与不承诺项

Phase 2 仍然不承诺：

```text
不证明 runtime reachability。
不解析任意地址上的真实运行时代码。
不根据链上状态判断 proxy 当前 implementation。
不替代人工审查 modifier、继承、override、low-level call。
不自动判断漏洞或攻击路径。
不保证 low-level call 能解析到具体函数。
```

文档和 README 必须明确说明：

```text
sol-callgraph 是 focused static call graph exporter。
它不是 execution graph、攻击路径搜索器或链上状态解析器。
```

## 4. Project Root 与编译上下文

### 4.1 背景

当前工具可以分析 OpenZeppelin 软链接路径，但真实 Solidity 项目里，Slither/solc import resolution 依赖 cwd、project root、Foundry/Hardhat 配置和 remappings。

如果用户从项目外执行：

```bash
sol-callgraph /project/contracts/Vault.sol
```

工具不应简单把绝对路径丢给 Slither，而应尽量模拟开发者手工运行：

```bash
cd /project
slither contracts/Vault.sol
```

### 4.2 新增 CLI

必须新增：

```text
--root <dir>
  显式指定 Solidity 项目根目录，并用该目录作为 Slither cwd。

--no-root-detect
  禁用自动 project root 查找，使用当前 cwd 和用户传入的 target。

--print-env
  打印 target、detected root、root reason、slither cwd、slither target、slither binary、slither python 后退出。
```

`--print-env` 是查询型命令，不输出 DOT。

### 4.3 Root 自动检测

从 target 文件所在目录向上查找 marker。

强 marker：

```text
foundry.toml
hardhat.config.ts
hardhat.config.js
hardhat.config.cjs
hardhat.config.mjs
truffle-config.js
truffle.js
brownie-config.yaml
ape-config.yaml
dapp.json
```

弱 marker：

```text
remappings.txt
package.json
.git
```

规则：

```text
优先返回最近的强 marker 所在目录。
弱 marker 只作为 fallback。
如果没有任何 marker，使用 target 文件所在目录。
```

### 4.4 传给 Slither 的 target

如果 target 在 root 内，应传相对 root 的路径给 Slither。

```text
target_abs = /a/b/c/contracts/Vault.sol
root = /a/b/c
slither target = contracts/Vault.sol
cwd = /a/b/c
```

如果 target 不在 root 内，则传绝对路径。

### 4.5 验证

必须增加 fixture 或临时测试项目：

```text
standalone file outside project marker
Foundry-like project with foundry.toml
monorepo with nested foundry.toml
package.json-only fallback
--root 覆盖自动检测
--no-root-detect 保持 cwd 行为
--print-env 输出稳定字段
```

## 5. Scope 与显示控制开关

Phase 1 默认 root scope 是目标文件/目标声明中 declared 且有实现的函数与 modifier。Phase 2 要增加显式开关，让用户在需要时扩大或缩小图。

### 5.1 `--include-inherited`

新增：

```text
--include-inherited
```

语义：

```text
默认：--contract Child 只把 Child 自己 declared 的函数/modifier 作为 root。
开启：把 Child 可见的继承函数/modifier 也作为 root。
```

要求：

```text
继承来的 root 节点必须通过 class 或 tooltip 标记 inherited。
默认行为不能改变。
```

### 5.2 `--include-interfaces`

新增：

```text
--include-interfaces
```

语义：

```text
默认：interface 函数不作为 root。
开启：interface 函数可以作为 root leaf 节点出现。
```

如果 interface 函数没有 body，不应尝试展开。

### 5.3 `--include-constructors` / `--no-constructors`

Phase 1 默认显示 constructor。Phase 2 应提供控制：

```text
--no-constructors
```

语义：

```text
默认显示 constructor。
开启 --no-constructors 后 root scope 不包含 constructor。
```

### 5.4 `--include-events`

新增：

```text
--include-events
```

语义：

```text
默认可以不显示 event emit，或只在当前行为已显示时保持兼容。
开启后 event emit 作为 builtin-like/event leaf 节点出现。
edge label = event。
```

### 5.5 `--include-errors`

新增：

```text
--include-errors / --no-errors
```

语义：

```text
默认显示 custom error / revert dotted leaf。
--no-errors 隐藏 custom error / revert leaf。
```

### 5.6 `--include-builtins`

新增：

```text
--include-builtins / --no-builtins
```

语义：

```text
默认显示 abi.decode / require / assert / keccak256 等 builtin leaf。
--no-builtins 隐藏 builtin leaf。
```

### 5.7 `--root-function`

新增：

```text
--root-function <canonical-or-unique-name>
```

可重复。

匹配规则：

```text
优先匹配完整 canonical name，例如 Vault.foo(uint256)。
允许短名，但只有唯一匹配时才接受。
如果短名匹配多个重载，必须报错并列出候选。
```

示例错误：

```text
error: function name `foo` is ambiguous
candidates:
  Vault.foo(uint256)
  Vault.foo(address)
```

## 6. 语义边与节点 metadata

### 6.1 Edge 类型分层

Phase 2 应明确区分：

```text
resolved edge
  静态可解析到具体函数。

symbolic edge
  只能知道发生 call/delegatecall/staticcall 等低级调用，无法知道真实函数。

builtin edge
  abi.decode / require / assert / keccak256 等内建操作。

event/error edge
  emit / revert custom error。

modifier edge
  function 受 modifier 包裹，不表示普通调用顺序。

override edge
  override/overrides 关系，不是执行边。
```

不要把这些边画成完全同一种语义。

### 6.2 `--include-overrides`

新增：

```text
--include-overrides
```

语义：

```text
显示 override / overrides 关系。
edge label = override 或 overrides。
该边不是 execution edge。
```

要求：

```text
默认关闭。
开启后必须通过 class 或 tooltip 标明 semantic edge / non-execution edge。
```

### 6.3 Initializer 标记

新增：

```text
--detect-initializers
--profile upgradeable
```

其中 `--profile upgradeable` 可以等价启用 initializer 识别。

识别规则：

```text
modifier: initializer
modifier: reinitializer
modifier: onlyInitializing
function name: initialize
function name: __*_init
function name: __*_init_unchained
```

行为：

```text
不隐藏 constructor。
给 initializer 相关节点加 class="initializer" 或 tooltip。
```

### 6.4 Entrypoint 标记

节点 metadata 应标记：

```text
external/public function
constructor
fallback
receive
initializer
```

例如：

```dot
class="root function entrypoint external"
class="root function entrypoint fallback"
class="root function entrypoint receive"
```

### 6.5 External Call Metadata

对于 high-level/interface/external call，尽量在 metadata 中保留：

```text
static target type
runtime target expression
function signature
```

DOT label 保持简洁，tooltip/class 放更多信息。

### 6.6 Library using-for Metadata

必须增加 using-for 测试，并尽量标记：

```text
direct library call
using-for library call
```

示例：

```solidity
using SafeERC20 for IERC20;
token.safeTransfer(to, amount);
```

期望图中能看出 `SafeERC20.safeTransfer` 语义，而不是只剩下裸 interface call。

## 7. 稳定 Node ID 与 DOT/SVG Metadata

### 7.1 稳定 Node ID

当前节点 ID 多数使用 canonical name。Phase 2 应进一步稳定化，避免不同文件同名 contract/function 冲突。

建议内部 ID：

```text
source_unit::contract::function_signature
```

显示 label 可以保持较短：

```text
Vault.withdraw(uint256)
```

要求：

```text
不得使用 Slither 对象 id、遍历序号或不稳定 hash 作为节点 ID。
```

### 7.2 DOT metadata

节点应尽量输出：

```text
label
class
tooltip
URL 或 id
source path
declaration kind
function kind
visibility
node role: root / expandable / builtin-like / unresolved
```

边应尽量输出：

```text
label
class
tooltip
edge semantic kind
resolved/symbolic 标记
```

### 7.3 SVG reader 预留

`--format svg` 输出不只是图片，应尽量保留 DOT metadata，方便未来 reader 解析 SVG DOM。

## 8. Cluster 与布局控制

新增：

```text
--cluster
--no-cluster
```

建议：

```text
Phase 2 可以默认不开 cluster，先用 --cluster 显式打开。
只对 root declarations 分 cluster。
external expandable / builtin / event / error 节点默认不放进 cluster。
```

如果未来决定默认开启 cluster，必须保留 `--no-cluster`。

## 9. 图规模保护与诊断

### 9.1 Max Nodes / Edges

新增：

```text
--max-nodes <n>
--max-edges <n>
```

默认建议：

```text
--max-nodes 500
--max-edges 1000
```

`0` 表示不限制。

达到限制时：

```text
输出 warning 到 stderr。
图可以是不完整图，但必须在 report/verbose 中说明 truncated。
提示用户用 --contract / --root-function / 降低 depth 缩小范围。
```

### 9.2 Unresolved 统计

verbose 模式下输出：

```text
unresolved calls:
  low_level: N
  high_level: N
  library: N
```

新增：

```text
--fail-on-unresolved
```

语义：

```text
如果存在 unresolved call，返回非 0。
适合 CI 或审计流程。
```

### 9.3 `--fail-on-warning`

新增：

```text
--fail-on-warning
```

语义：

```text
如果产生 warning，最终返回非 0。
```

## 10. Slither/solc 参数与日志

### 10.1 Slither/solc 参数透传

新增能力：

```text
--solc-remaps <value>
--solc-args <value>
--compile-force-framework <foundry|hardhat|brownie|truffle>
--slither-arg <arg>
```

实现可以分阶段：

```text
先实现 --slither-arg 可重复透传。
再实现常用语义化参数。
```

要求：

```text
参数必须只影响 Slither 初始化/编译，不影响 stdout DOT 纯净性。
--print-env 应显示透传参数。
```

### 10.2 Slither warning 与 debug

新增：

```text
--debug-slither
```

行为：

```text
显示完整 Slither 调用环境、cwd、target、Slither Python、root reason、透传参数。
不要吞掉 Slither/solc warning。
--quiet 只抑制 warning/info，不抑制 error。
```

## 11. JSON 输出

新增：

```text
--format json
```

JSON 应包含：

```text
schema_version
target
project_root
root_scope
nodes[]
edges[]
warnings[]
stats
tool_version
slither_version
```

节点至少包含：

```text
id
label
kind
role
source
source_location
declared_contract
declared_contract_kind
contract
viewed_as_contract
signature
visibility
classes
tooltip
```

`source_location` 来自 Slither `source_mapping`，用于机器消费和源码跳转，
不要依赖 tooltip 或函数名正则推断声明位置。它应包含源文件路径、绝对路径、
起止行列以及可用的源码 offset/length。

边至少包含：

```text
src
dst
kind
resolved
classes
tooltip
```

JSON 输出必须和 DOT 一样保持 stdout 纯净。

## 12. Cache 策略

Phase 2 不强制实现缓存，但必须在 TODO 中记录。

如果实现缓存，cache key 至少包含：

```text
target absolute path
target file hash 或 mtime
project root
foundry/hardhat/truffle/brownie config hash
remappings.txt hash
sol-callgraph version
slither version
depth
contract filters
root function filters
include flags
format
```

默认不要开启不可靠缓存。

## 13. Stdin 支持

Phase 2 仍建议不支持 stdin。

如果用户传：

```bash
sol-callgraph -
```

应明确报错：

```text
error: stdin input is not supported; sol-callgraph needs a real file path for Slither/import resolution
```

## 14. 测试矩阵扩展

Phase 2 必须新增“恶心样例”fixture，不只依赖 OpenZeppelin。

至少覆盖：

```text
single file, one contract
single file, contract + interface + library
multiple contracts with same function names
function overload
modifier with internal calls
constructor calling parent constructor
fallback/receive
low-level call
delegatecall
staticcall
using-for library
custom error revert
event emit
interface call
inheritance override
abstract contract
proxy-like dynamic implementation
file outside git/project
Foundry-like project
monorepo with nested foundry.toml
package.json fallback
```

每个 fixture 要记录：

```text
当前支持行为
期望边
期望节点 metadata
是否应该 warning
是否应该 unresolved
```

## 15. README 与帮助信息

README 需要从当前极简说明升级为可用文档。

必须包含：

```text
安装和开发环境
基础用法
project root 行为
scope 控制
depth 说明
输出格式
不承诺项
OpenZeppelin selftest
常见错误
```

CLI help 必须列出所有真实支持的参数。launcher-only 参数不能只写在 description 里，至少 README 要有独立说明。

## 16. Phase 2 建议实施顺序

建议 Gemini 或其他编程 AI 按顺序实施：

```text
1. Project root 检测：--root / --no-root-detect / --print-env。
2. README 和 help 更新。
3. Scope 控制：--include-inherited / --include-interfaces / --root-function。
4. 显示控制：--no-builtins / --no-errors / --include-events / --no-constructors。
5. 语义 metadata：entrypoint、initializer、external call、using-for。
6. Override 边：--include-overrides。
7. 稳定 node id 和 DOT metadata。
8. Cluster：--cluster / --no-cluster。
9. 图规模保护和 unresolved 统计。
10. Slither 参数透传和 --debug-slither。
11. JSON 输出。
12. 扩展 fixture 矩阵和 OpenZeppelin selftest。
```

每一步必须保持：

```text
./.venv/bin/python -m pytest
./.venv/bin/python -m sol_callgraph.selftest_openzeppelin
make test-all
```

通过，或明确记录失败原因。

## 17. Phase 2 完成标准

Phase 2 完成时必须满足：

```text
新增 CLI 都有测试。
README 与 --help 不误导用户。
project root 行为可由 --print-env 解释。
默认输出仍与 Phase 1 兼容。
显式 include 开关不会意外改变默认图。
OpenZeppelin selftest 仍为 0 failures。
新增 fixture 覆盖第 14 节主要场景。
TODO.md 中没有未登记的已知缺口。
```
