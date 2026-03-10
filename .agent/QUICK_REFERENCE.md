# 智能体框架快速参考

## 🚀 快速开始

```bash
# 查看项目状态
./.agent/agent.sh status

# 查看下一个任务
./.agent/agent.sh next

# 查看待办列表
./.agent/agent.sh todo

# 启动开发环境
./.agent/init.sh
```

## 📁 核心文件

| 文件 | 用途 | 读取频率 |
|------|------|----------|
| `feature_list.json` | 功能清单 | 每次会话 |
| `claude-progress.txt` | 工作日志 | 每次会话 |
| `init.sh` | 启动脚本 | 开发时 |
| `AGENT_FRAMEWORK.md` | 框架文档 | 参考 |

## 🔄 会话流程

### 开始会话
```bash
# 1. 检查 Git 状态
git status
git log --oneline -5

# 2. 读取状态文件
cat .agent/claude-progress.txt
cat .agent/feature_list.json | jq '.features[] | select(.passes == false)'
```

### 结束会话
```bash
# 1. 提交代码
git add .
git commit -m "feat(xxx): 描述"

# 2. 更新状态
# 编辑 feature_list.json: passes: false → true
# 编辑 claude-progress.txt: 添加会话记录
```

## ⚠️ 重要约束

- ❌ 不删除功能项
- ❌ 不修改测试用例
- ✅ 只更新 passes 状态
- ✅ 必须验证测试通过

## 📊 功能状态

```bash
# 查看完成进度
cat .agent/feature_list.json | jq '
  {
    total: (.features | length),
    done: ([.features[] | select(.passes == true)] | length),
    todo: ([.features[] | select(.passes == false)] | length)
  }
'
```

## 🔗 相关资源

- 详细文档: `.agent/AGENT_FRAMEWORK.md`
- 初始化提示词: `.agent/prompts/initializer.md`
- 编码提示词: `.agent/prompts/coding.md`
