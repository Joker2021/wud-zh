# WUD 简体中文版构建

本项目从 WUD 官方**已发布稳定 Release 的固定 commit**构建，不维护 WUD 后端分叉。它以 Vue 编译器 AST 提取和替换 UI 模板中的静态英文文本，使用有道智云翻译新增文案，并在翻译覆盖、上游构建和测试通过后发布多架构 GHCR 镜像。

当前发布基线为 WUD 9.6.0（上游 commit `ae3c0827c020e62ba15b8df6edd5b04aa05e9e62`）。[Joker2021/wud-zh](https://github.com/Joker2021/wud-zh) 是此项目的 fork；[9.6.0 简体中文版镜像](https://github.com/Joker2021/wud-zh/releases/tag/wud-9.6.0-zh.1) 已发布，地址为 `ghcr.io/joker2021/wud-zh:9.6.0-zh.1`。

## 本地翻译流程

准备 WUD 对应 Release 的完整源码，先在 `ui/` 执行 `npm ci`，再运行：

```sh
node scripts/i18n.mjs extract --upstream /path/to/wud --output /tmp/wud-strings.json
python3 scripts/translate.py /tmp/wud-strings.json --version 9.6.0 --dry-run
```

首次 9.6.0 翻译由 Codex 离线完成（331 个键、236 条不同原文，没有调用有道；译文尚待人工复核）。后续自动流程复用翻译记忆，只有未缓存的新文案才调用有道。若要手动翻译缓存未命中文案，设置 `YOUDAO_APP_KEY` 与 `YOUDAO_APP_SECRET` 后去掉 `--dry-run`：

```sh
python3 scripts/translate.py /tmp/wud-strings.json --version 9.6.0
node scripts/i18n.mjs apply --upstream /path/to/wud --translations translations/zh-CN.json
```

不要在包含密钥的 shell 输出或日志中打印环境变量。Actions 配置方法见[文档](docs/github-setup.md)。

## 部署

复制 [`deploy/docker-compose.yml`](deploy/docker-compose.yml) 到绿联 Docker 的 Compose 项目，先填入 GHCR 镜像地址、管理员用户名和密码，再启动。部署和回滚见[绿联 NAS 指南](docs/nas-deployment.md)。

## 安全和翻译边界

- 示例默认不开启容器更新 Trigger；只监控 Docker 镜像更新。
- Docker Socket 提供高权限 Docker API，`/var/run/docker.sock:ro` 也不等于只读 API。仅挂到可信容器。
- 只发送上游 UI 静态文案到有道，不发送 NAS 配置、容器变量或用户数据。
- 当前覆盖 `.vue` 模板中的静态文本以及 `placeholder`、`title`、`aria-label`、`alt`、`label` 属性。脚本生成的动态消息、后端英文响应及运行时语言切换未覆盖。
- 官方新稳定版触发自动翻译和兼容性检查；通过后自动更新 fork 的 `main` 并派发构建。只有多架构构建及烟测通过才更新 GHCR 稳定标签。没有翻译 Secret 时只可复用全部缓存，否则工作流失败关闭。

## 验证

```sh
python3 -m unittest discover -s tests -v
```

项目测试检查脚本签名、占位符、缓存和失败原子性。9.6.0 上游测试、翻译覆盖门禁、多架构构建、amd64 容器烟测及 GHCR 发布已由[首次发布工作流](https://github.com/Joker2021/wud-zh/actions/runs/40221070914)验证；ARM64 运行时和真实绿联环境仍未验证。

更多信息：[`docs/upstream-analysis.md`](docs/upstream-analysis.md)、[`docs/architecture.md`](docs/architecture.md)、[`PROJECT_HANDOFF.md`](PROJECT_HANDOFF.md)。
