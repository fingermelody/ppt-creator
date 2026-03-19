---
description: 提交代码到远程仓库：自动检查分支、代码质量、add/commit/push
type: manual
---

# MR - 提交代码

## 执行步骤

### 1. 检查 Git 状态
```bash
git branch --show-current
git status
git diff --stat
```

### 2. 分支保护检查
- 如果当前在 `main` 或 `master` 分支：
  - 提示用户："当前在主分支，建议先创建功能分支。是否继续？"
  - 如用户确认则继续，否则终止

### 3. 获取 Commit Message
- 如果用户输入已提供 message（如 "mr 修复登录bug"），直接使用
- 否则询问用户 commit message

### 4. 代码质量检查（可选）
- 如项目有 lint 配置：
  - JavaScript/TypeScript: 运行 `npm run lint` 或 `yarn lint`
  - Python: 运行 `ruff check .` 或 `flake8`
- 如检查失败，询问是否继续

### 5. 提交代码
```bash
git add .
git commit -m "<message>"
```

### 6. 推送到远程
```bash
git push -u origin <current-branch>
```

### 7. 输出结果
显示提交成功信息，包含：
- 提交 hash
- 提交 message
- 分支信息

## 注意事项
- 使用 `-u` 参数自动跟踪远程分支
- commit message 建议遵循 Conventional Commits 格式
- 提交前确认所有文件都已正确添加
