# sol-callgraph TODO List

## 核心功能 (Core Features)
- [x] 默认以目标文件为 root scope
- [x] 支持通过 `--contract` 指定特定合约/库为 root
- [x] 默认输出标准 DOT 到 stdout
- [x] 诊断、warning 和日志输出到 stderr
- [x] 完整保留 Slither 识别的所有调用类型 (internal, solidity, high-level, library, low-level)
- [x] 外部可解析函数显示为 expandable 节点 (dashed box)
- [x] 基于 `--depth` 的受限 BFS 展开模型
- [x] 节点分类与样式渲染 (root, expandable, builtin-like, unresolved)
- [x] 完善的 DOT 字符串与 ID 转义
- [x] 支持输出 SVG 和 PNG 格式 (依赖 Graphviz)
- [x] 支持列出目标文件中的声明 (`--list-contracts`)
- [x] Modifier 调用支持
- [x] 多声明文件处理逻辑
- [x] 自动探测 Slither 环境 (支持 pyenv shims 识别)
- [x] 根目录包装脚本快捷方式 (`./sol-callgraph`)
- [x] 优化的 CLI 交互体验 (报错自动打印 Help)

## 测试与验证 (Testing & Validation)
- [x] 基础单元测试 (DOT 渲染逻辑)
- [x] 小型 Fixture 集成测试
- [x] OpenZeppelin 真实项目智能自测脚本
- [x] 自动化测试报告生成 (test-artifacts/report.md)

## 待实现 / 增强 (Future Enhancements)
- [ ] `--root-function <canonical-name>`: 从指定函数开始绘图
- [ ] `--include-interfaces`: 强制在 root 中包含 interface 函数
- [ ] `--include-events`: 可配置是否显示 event emit
- [ ] `--include-errors`: 可配置是否显示 custom error/revert
- [ ] `--include-builtins`: 可配置是否隐藏 abi.decode/require 等内置调用
- [ ] `--no-cluster`: 支持按声明进行 cluster 分组，并提供开关
- [ ] `--fail-on-warning`: CI 模式，warning 视为失败
- [ ] 支持透传 Slither/solc 的额外参数 (remappings, solc-args 等)
- [ ] 支持输出 JSON 格式的 graph 供其他工具消费
- [ ] 增强 SVG 输出: 增加 URL、Tooltip 和 CSS Class 支持
