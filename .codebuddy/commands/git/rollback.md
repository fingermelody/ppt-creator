---
description: 回滚代码：支持 soft/mixed/hard/revert 多种回滚方式，带确认机制
type: manual
---

# Rollback - 回滚代码

## 执行步骤

### 1. 显示当前状态
```bash
git log --oneline -10
git status
```

### 2. 询问回滚方式
提供以下选项让用户选择：

**选项 1: 软回滚（推荐）**
```bash
git reset --soft HEAD~1
```
- 保留工作区和暂存区修改
- 仅撤销 commit
- 可重新修改后再次提交

**选项 2: 混合回滚（默认）**
```bash
git reset HEAD~1
```
- 保留工作区修改
- 清空暂存区
- 适合调整 commit

**选项 3: 硬回滚（危险）**
```bash
git reset --hard HEAD~1
```
- ⚠️ 丢弃所有修改
- 完全回到上次提交
- 需要用户二次确认

**选项 4: 回滚到指定提交**
```bash
git reset --hard <commit-hash>
```
- 回滚到指定 hash
- ⚠️ 需要用户二次确认

**选项 5: Revert（已推送的提交）**
```bash
git revert <commit-hash>
```
- 生成新提交来撤销
- 不修改历史
- 适合已推送的提交

### 3. 执行回滚
- 执行选定命令
- 显示回滚结果

### 4. 后续处理建议
- 如有修改，提示：
  - `git status` 查看当前状态
  - `git diff` 查看具体变更
  - `git commit -am "message"` 重新提交
- 如已推送，提示需要 `git push -f`

## 注意事项
- hard 操作不可逆，必须二次确认
- 已推送到远程的提交建议使用 revert
- 回滚前务必确认提交 hash 正确
- 重要操作前建议先创建备份分支
