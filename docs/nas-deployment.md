# NAS 部署

## 绿联

1. 绿联 Docker 的 Compose 项目选择目录 `/volume1/docker/AppData/wud-zh`，并使用 [`deploy/docker-compose.ugreen.yml`](../deploy/docker-compose.ugreen.yml)。该文件固定使用当前镜像 `ghcr.io/joker2021/wud-zh:9.6.0-zh.2`；容器数据保存在子目录 `/volume1/docker/AppData/wud-zh/data`。不要覆盖其他项目文件。
2. 在 Container Manager 的 Compose 项目环境变量中设置 `WUD_AUTH_ADMIN_USER` 和强密码 `WUD_AUTH_ADMIN_PASSWORD`。Compose 会在缺少任一变量时停止启动。不要将真实凭据写入或分享 Compose 文件；镜像升级时再将文件中的固定 tag 改为审核通过的新版本。
3. 如 GHCR package 为私有，在绿联 Docker 中登录 GHCR 并确认有 pull 权限；优先将镜像设为公开以避免设备保存 PAT。
4. 启动后访问 `http://NAS地址:12712` 并使用管理员账号登录。若端口冲突，编辑 `deploy/docker-compose.ugreen.yml` 中的宿主端口映射 `12712:3000` 左侧端口，改用未占用端口。
5. 容器默认本地 Docker watcher 检查镜像更新，自动更新 Trigger 未配置。先在 WUD 界面查看更新；手动升级本 Compose 项目到审核后的新固定镜像版本。
6. 更新前备份 bind mount 目录 `/volume1/docker/AppData/wud-zh/data`；保留旧版本镜像 tag。若升级后异常，Compose 改回上一成功 tag 并重启，同时保留该目录中的数据。

Docker Socket 挂载仅用于检测本机容器镜像。Socket 即使写成 `:ro` 仍暴露强权限 Docker API。不要把 WUD 端口公开到不可信网络；使用内网访问或反向代理认证/TLS。

NAS Docker daemon 拉取 GHCR 失败时，检查 DNS/出口、系统时间、GHCR 凭据和镜像名/tag。需要代理时只配置绿联 Docker daemon 支持的代理入口并重启 Docker 服务；具体菜单随 UGOS 版本变化，请以设备现有设置为准。Compose Trigger 后续只有在确需自动改 Compose 文件时才配置；需将原始 Compose 文件挂载到容器内可写路径并授予必要目录权限，且会改变 NAS 工作负载，应单独审核。

固定的 `ghcr.io/joker2021/wud-zh:9.6.0-zh.2` 基于上游 `9.6.0`；它不支持 `WUD_AUTH_SESSION_SECRET`，设置该变量会被解释为未知的 `session` 认证 provider。此 Compose 示例通过专用 bridge network 固定容器 MAC，让上游 `getmac` 回退能读到非零 MAC。不要改用 host 网络模式：它的端口映射行为不同，且不是本示例默认方案。MAC 应保持不变；更换后可能导致现有登录会话失效。

截至 2026-10-27，绿联 NAS 尚未由本项目连接、操作或部署；以上 bridge/MAC workaround 仍需在真实绿联设备验证。
