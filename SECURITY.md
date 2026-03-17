# 安全最佳实践

## 🔒 密钥管理

### 1. 环境变量配置

**正确做法** ✅
```bash
# .env 文件（已在 .gitignore 中）
TENCENT_SECRET_ID=your-actual-secret-id
TENCENT_SECRET_KEY=your-actual-secret-key
```

**错误做法** ❌
```bash
# 不要在代码中硬编码
secret_id = "AKID_REDACTED_SECRET_ID"
```

### 2. 提交前检查

在提交代码前，请确保：

```bash
# 检查是否有敏感信息
git diff | grep -i "secret\|password\|key"

# 检查暂存区
git diff --cached | grep -i "secret\|password\|key"
```

### 3. Git 历史清理

如果不小心提交了敏感信息，需要从 Git 历史中彻底删除：

```bash
# ⚠️ 警告：这会重写 Git 历史
git filter-branch --force --index-filter \
  "git rm --cached --ignore-unmatch PATH/TO/FILE" \
  --prune-empty --tag-name-filter cat -- --all

# 强制推送（需谨慎）
git push origin --force --all
```

更安全的方法是使用 BFG Repo-Cleaner：
```bash
brew install bfg
bfg --replace-text passwords.txt  # 文件包含要删除的密钥列表
```

### 4. 密钥轮换

定期轮换密钥以提高安全性：

1. 在腾讯云控制台创建新密钥
2. 更新所有环境的 `.env` 文件
3. 更新 GitHub Secrets
4. 删除旧密钥

## 📋 检查清单

提交代码前请确认：

- [ ] `.env` 文件已添加到 `.gitignore`
- [ ] 所有示例文件使用占位符（如 `your-secret-id`）
- [ ] GitHub Secrets 已正确配置
- [ ] 文档中不包含真实密钥
- [ ] Kubernetes ConfigMap/Secret 不包含明文密钥

## 🚨 发现泄露怎么办？

如果发现密钥泄露：

1. **立即轮换密钥**
   - 在腾讯云控制台禁用泄露的密钥
   - 创建新密钥并更新所有环境

2. **清理 Git 历史**
   - 使用上述方法从历史记录中删除

3. **通知团队**
   - 告知所有团队成员更新密钥

4. **审查访问日志**
   - 检查腾讯云访问日志，确认是否有异常访问

## 📚 参考资源

- [腾讯云密钥管理最佳实践](https://cloud.tencent.com/document/product/598/10598)
- [GitHub Secrets 文档](https://docs.github.com/en/actions/security-guides/encrypted-secrets)
- [Git 敏感信息清理](https://docs.github.com/en/authentication/keeping-your-account-and-data-secure/removing-sensitive-data-from-a-repository)
