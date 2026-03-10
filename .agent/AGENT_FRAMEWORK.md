# PPT-RSD 长时间运行智能体框架

> 基于 Anthropic 《Effective Harnesses for Long-Running Agents》最佳实践

## 📋 概述

本框架旨在解决 AI 智能体在长时间运行、多会话场景下的问题：

1. **上下文断裂** - 多轮会话后记忆丢失
2. **任务追踪困难** - 无法准确知道完成了什么、待做什么
3. **过早宣告完成** - 在功能未完全实现时声称完成
4. **工作交接困难** - 新会话无法快速接手工作

## 🏗️ 核心架构

### 双代理模式

```
┌─────────────────────────────────────────────────────────────┐
│                        项目生命周期                          │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│  ┌──────────────────┐        ┌──────────────────┐          │
│  │  初始化代理      │        │   编码代理        │          │
│  │  (Initializer)   │───────▶│   (Coding)       │          │
│  │                  │  一次   │                  │          │
│  │  - 创建项目结构   │        │  - 增量实现功能   │          │
│  │  - 定义功能清单   │        │  - 自我验证测试   │          │
│  │  - 搭建开发环境   │        │  - 更新进度状态   │          │
│  │  - 初始化Git     │        │  - 提交干净代码   │          │
│  └──────────────────┘        └──────────────────┘          │
│         │                            │                      │
│         │                            │                      │
│         ▼                            ▼                      │
│  ┌─────────────────────────────────────────────────────┐   │
│  │              外部状态存储 (Artifacts)                 │   │
│  ├─────────────────────────────────────────────────────┤   │
│  │  • feature_list.json  - 机器可读的功能清单           │   │
│  │  • claude-progress.txt - 人类可读的工作日志          │   │
│  │  • Git 历史           - 代码变更追溯                 │   │
│  │  • init.sh            - 环境启动脚本                 │   │
│  └─────────────────────────────────────────────────────┘   │
│                                                              │
└─────────────────────────────────────────────────────────────┘
```

## 📁 文件结构

```
PPT-RSD/
├── .agent/                      # 智能体框架目录
│   ├── feature_list.json        # 功能清单 (机器可读)
│   ├── claude-progress.txt      # 工作日志 (人类可读)
│   ├── init.sh                  # 启动脚本
│   ├── AGENT_FRAMEWORK.md       # 本文档
│   └── prompts/                 # 代理提示词模板
│       ├── initializer.md       # 初始化代理提示词
│       └── coding.md            # 编码代理提示词
├── backend/                     # 后端代码
├── frontend/                    # 前端代码
└── tests/                       # 测试代码
```

## 🔄 工作流程

### 初始化代理 (首次运行)

```
┌─────────────────────────────────────────────────────────────┐
│                    初始化代理工作流                          │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│  1. 解析项目目标                                              │
│     └─▶ 理解用户需求，拆解为端到端功能                         │
│                                                              │
│  2. 创建功能清单                                              │
│     └─▶ 生成 feature_list.json，所有功能 passes: false        │
│                                                              │
│  3. 创建启动脚本                                              │
│     └─▶ 编写 init.sh，标准化环境启动                          │
│                                                              │
│  4. 初始化 Git                                                │
│     └─▶ 创建仓库并提交基线版本                                 │
│                                                              │
│  5. 创建工作日志                                              │
│     └─▶ 写入项目目标、范围、初始状态                           │
│                                                              │
└─────────────────────────────────────────────────────────────┘
```

### 编码代理 (后续会话)

```
┌─────────────────────────────────────────────────────────────┐
│                    编码代理工作流                            │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│  1. 状态同步                                                  │
│     ├─▶ pwd                  # 确认工作目录                   │
│     ├─▶ git log --oneline -10  # 查看最近提交                │
│     ├─▶ cat claude-progress.txt # 阅读工作日志               │
│     └─▶ cat feature_list.json   # 查看功能清单               │
│                                                              │
│  2. 任务选择                                                  │
│     └─▶ 从功能清单中选择优先级最高且 passes: false 的功能      │
│                                                              │
│  3. 环境验证                                                  │
│     └─▶ 运行 ./init.sh 启动服务，执行冒烟测试                  │
│                                                              │
│  4. 实现功能                                                  │
│     └─▶ 编写代码 + 单元测试 + 端到端测试                       │
│                                                              │
│  5. 自我验证                                                  │
│     ├─▶ 运行自动化测试                                        │
│     ├─▶ 启动应用手动验证                                      │
│     └─▶ 执行功能测试列表中的所有测试                           │
│                                                              │
│  6. 提交记录                                                  │
│     ├─▶ git commit -m "feat: 实现XXX功能"                     │
│     ├─▶ 更新 feature_list.json 中对应功能的 passes: true      │
│     └─▶ 更新 claude-progress.txt 记录本次会话                 │
│                                                              │
│  7. 清理退出                                                  │
│     ├─▶ 终止所有后台进程                                      │
│     └─▶ 确保工作目录干净                                      │
│                                                              │
└─────────────────────────────────────────────────────────────┘
```

## 📝 核心文件规范

### feature_list.json 结构

```json
{
  "project": "项目名称",
  "version": "版本号",
  "features": [
    {
      "id": "feat-001",
      "category": "core|infrastructure|ai|export|collaboration",
      "name": "功能名称",
      "description": "详细描述",
      "priority": "high|medium|low",
      "passes": false,
      "tests": [
        "测试用例1",
        "测试用例2"
      ]
    }
  ],
  "constraints": {
    "禁止删除功能项": "代理不得删除任何功能项",
    "仅更新状态": "只能将 passes 从 false 改为 true",
    "保持测试完整性": "不得修改 tests 数组"
  }
}
```

### claude-progress.txt 格式

```ini
=== 项目名称 - Claude 工作日志 ===
项目: 项目描述
目标: 项目目标
开始时间: YYYY-MM-DD

=== 会话 N - YYYY-MM-DD ===
目标: 本次会话目标
完成:
- 完成的任务1
- 完成的任务2
遇到的问题:
- 问题描述
下次继续: 下一步计划

Git commits:
- abc1234 feat: 提交信息

=== 状态同步检查点 ===
当前分支: 分支名
已完成功能: X/Y
待完成功能: Z 个 (feat-xxx, ...)
```

## 🎯 最佳实践

### 1. 每次会话开始时

```bash
# 1. 确认工作目录
pwd

# 2. 查看 Git 状态
git status
git log --oneline -10

# 3. 阅读工作日志
cat .agent/claude-progress.txt

# 4. 查看功能清单
cat .agent/feature_list.json | jq '.features[] | select(.passes == false)'
```

### 2. 实现功能时

- **专注单一功能** - 每次会话只实现一个功能
- **测试驱动** - 先写测试，再写实现
- **小步提交** - 频繁提交，保持提交历史清晰

### 3. 完成功能后

```bash
# 1. 运行测试
npm test  # 或 pytest

# 2. 启动服务验证
./.agent/init.sh

# 3. 提交代码
git add .
git commit -m "feat(xxx): 实现XXX功能"

# 4. 更新状态
# 编辑 feature_list.json，将 passes 改为 true
# 编辑 claude-progress.txt，记录本次会话

# 5. 清理环境
# 终止后台进程，确保工作目录干净
```

### 4. 遇到阻塞时

- 在 claude-progress.txt 中详细记录问题
- 不要强制标记 passes: true
- 留下清晰的上下文供下次会话接手

## ⚠️ 重要约束

### 代理禁止行为

1. **❌ 禁止删除功能项** - 不得从 feature_list.json 中删除任何功能
2. **❌ 禁止修改测试用例** - 不得修改功能的 tests 数组内容
3. **❌ 禁止批量标记完成** - 必须逐个验证后才能更新状态
4. **❌ 禁止跳过验证步骤** - 必须执行完整的自我验证

### 代理必须行为

1. **✅ 必须读取状态文件** - 每次会话开始时同步状态
2. **✅ 必须更新进度** - 每次会话结束时更新 claude-progress.txt
3. **✅ 必须提交干净代码** - 提交前确保代码可运行
4. **✅ 必须清理环境** - 会话结束时终止后台进程

## 🔧 工具集成

### 与 Claude Code 集成

在 `.codebuddy/rules/` 中定义项目规则，让 Claude Code 自动遵循此框架：

```markdown
# 长时间运行智能体规则

## 会话开始时
1. 读取 .agent/claude-progress.txt 了解历史
2. 读取 .agent/feature_list.json 确认待办
3. 选择优先级最高的未完成功能

## 会话结束时
1. 更新 feature_list.json 中功能状态
2. 更新 claude-progress.txt 记录进度
3. 确保所有进程已清理
```

### 与 CI/CD 集成

```yaml
# .github/workflows/agent-check.yml
name: Agent Framework Check
on: [push, pull_request]

jobs:
  check:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      
      - name: Validate feature_list.json
        run: |
          # 检查 JSON 格式
          jq . .agent/feature_list.json
          # 检查是否有 passes 字段
          jq '.features[].passes' .agent/feature_list.json
          
      - name: Check progress file
        run: |
          test -f .agent/claude-progress.txt
```

## 📊 进度追踪

### 查看整体进度

```bash
# 已完成功能数量
jq '[.features[] | select(.passes == true)] | length' .agent/feature_list.json

# 待完成功能列表
jq '.features[] | select(.passes == false) | {id, name, priority}' .agent/feature_list.json

# 按优先级统计
jq '.features | group_by(.priority) | map({priority: .[0].priority, count: length})' .agent/feature_list.json
```

### 查看特定功能详情

```bash
# 查看某个功能的详细信息
jq '.features[] | select(.id == "feat-001")' .agent/feature_list.json
```

## 🚀 快速开始

### 新会话检查清单

- [ ] 确认当前分支和 Git 状态
- [ ] 阅读 claude-progress.txt 了解上次会话
- [ ] 查看 feature_list.json 选择下一个任务
- [ ] 运行 init.sh 启动开发环境
- [ ] 实现功能并验证
- [ ] 提交代码并更新状态文件
- [ ] 清理环境退出

### 命令速查

```bash
# 启动环境
./.agent/init.sh

# 查看待办功能
cat .agent/feature_list.json | jq '.features[] | select(.passes == false)'

# 查看进度
cat .agent/claude-progress.txt

# 提交完成
git add . && git commit -m "feat: 完成功能"
# 然后更新 feature_list.json 和 claude-progress.txt
```

## 📚 参考资料

- [Anthropic: Effective Harnesses for Long-Running Agents](https://www.anthropic.com/engineering/effective-harnesses-for-long-running-agents)
- [Claude Code 文档](https://docs.anthropic.com/claude/docs/claude-code)

---

**维护者**: PPT-RSD 开发团队  
**最后更新**: 2026-03-10
