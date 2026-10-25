# 绿联 NAS 部署

1. 先确认 GHCR 镜像已发布，复制 `deploy/docker-compose.yml` 到绿联 Docker 的 Compose 项目。参考 `deploy/.env.example` 填入实际镜像地址和凭据；不要覆盖现有项目文件，也不要公开真实 `.env`。
2. 在 Compose 项目环境变量中设置 `WUD_IMAGE` 为已发布的**固定版本**，例如 `ghcr.io/你的组织/wud-zh:9.6.0-zh.1`；设置 `WUD_AUTH_ADMIN_USER` 和强密码 `WUD_AUTH_ADMIN_PASSWORD`。不要把含真实密码的 Compose 文件公开。
3. 如 GHCR package 为私有，在绿联 Docker 中登录 GHCR 并确认有 pull 权限；优先将镜像设为公开以避免设备保存 PAT。
4. 启动后访问 `http://NAS地址:3000` 并使用管理员账号登录。端口可通过 `WUD_HOST_PORT` 改为未占用端口。
5. 容器默认本地 Docker watcher 检查镜像更新，自动更新 Trigger 未配置。先在 WUD 界面查看更新；手动升级本 Compose 项目到审核后的新固定镜像版本。
6. 更新前备份命名卷 `wud-data`；保留旧版本镜像 tag。若升级后异常，Compose 改回上一成功 tag 并重启。不要清除 `/store` 数据卷。

Docker Socket 挂载仅用于检测本机容器镜像。Socket 即使写成 `:ro` 仍暴露强权限 Docker API。不要把 WUD 端口公开到不可信网络；使用内网访问或反向代理认证/TLS。

NAS Docker daemon 拉取 GHCR 失败时，检查 DNS/出口、系统时间、GHCR 凭据和镜像名/tag。需要代理时只配置绿联 Docker daemon 支持的代理入口并重启 Docker 服务；具体菜单随 UGOS 版本变化，请以设备现有设置为准，不要照搬群晖路径。Compose Trigger 后续只有在确需自动改 Compose 文件时才配置；需将原始 Compose 文件挂载到容器内可写路径并授予必要目录权限，且会改变 NAS 工作负载，应单独审核。
