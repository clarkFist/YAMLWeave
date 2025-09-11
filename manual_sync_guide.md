# YAMLWeave 手动同步指南

## 当前状态
- ✅ 本地代码已提交到最新版本: `9749ead`
- 🔄 自动重试脚本正在后台运行 (还有13次尝试)
- 📦 已创建多种备份方案

## 可用的同步方案

### 方案1: 等待自动同步 (推荐)
- `sync_retry.sh` 脚本正在后台运行
- 使用指数退避策略，最多20次重试
- 一旦网络恢复会自动完成同步

### 方案2: Git Bundle 离线传输
```bash
# 已创建: yamlweave-backup.bundle (包含完整git历史)
# 在网络良好的环境中使用:
git clone --bare yamlweave-backup.bundle temp-repo
cd temp-repo
git remote add origin https://github.com/clarkFist/YAMLWeave.git
git push origin --all
git push origin --tags
```

### 方案3: 压缩包手动上传
- 已创建: `yamlweave-project.tar.gz`
- 可直接在GitHub网页界面上传所有文件

### 方案4: 强制推送 (网络恢复时)
```bash
git push -u origin main --force --ipv4
```

### 方案5: 重新创建仓库
1. 删除 https://github.com/clarkFist/YAMLWeave 仓库
2. 重新创建同名仓库
3. 执行: `git push -u origin main`

## 网络配置优化 (已应用)
- HTTP缓冲区: 1GB
- 压缩: 禁用
- IPv4强制连接
- SSL验证: 启用

## 文件清单
- `sync_retry.sh`: Linux/WSL自动重试脚本
- `sync_retry.bat`: Windows自动重试脚本  
- `alternative_sync.sh`: 备用同步策略
- `yamlweave-backup.bundle`: Git bundle备份
- `yamlweave-project.tar.gz`: 压缩包备份

## 监控重试状态
```bash
# 查看后台脚本输出
ps aux | grep sync_retry
# 或检查错误日志
tail -f nohup.out
```

网络恢复后任意方案都能成功同步到 https://github.com/clarkFist/YAMLWeave.git