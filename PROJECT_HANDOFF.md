# wud-zh 接手文档

## 目标与边界

跟踪 WUD 已发布稳定版，为其 Vue UI 生成简体中文版本；自动化在 GitHub Actions 运行。工程已发布到 [Joker2021/wud-zh](https://github.com/Joker2021/wud-zh)，这是 `getwud/wud` 的 fork。上游 `ci.yml` 已在 fork 的 GitHub Actions 中禁用；本工程不会连接或修改用户 NAS。

## 当前版本与发布状态

- 本次核对基线：WUD `9.6.0`，上游 commit `ae3c0827c020e62ba15b8df6edd5b04aa05e9e62`。官方 Release 页面标为 Latest，发布日期 2026-10-24。
- 尚未产生中文版镜像；`WUD_IMAGE=ghcr.io/Joker2021/wud-zh` 已配置，Actions 已启用。9.6.0 的 331 条静态文案已由 Codex 离线翻译并写入记忆库（236 条不同原文，0 次有道请求，尚未人工复核）。
- 工作区没有构建或 NAS 运行验证。完整状态见 `docs/upstream-analysis.md`。

## 关键目录

- `scripts/`：上游 Release 检测、Vue 静态文案提取/应用、有道 API 翻译。
- `translations/`：简体中文覆盖、持久翻译记忆和术语表。
- `.github/workflows/`：Release 检查、翻译更新、构建与发布。
- `deploy/`：绿联 NAS Compose 示例。
- `docs/`：分析、架构、密钥设置、部署和排错。
- `.codex/skills/wud-zh/SKILL.md`：本项目稳定维护规则。

## 已检查与未检查

- 已核对官方 9.6.0 Release、源码标签、UI package manifest、Dockerfile、Actions 多架构配置、MIT 许可证和 Youdao 文本翻译 API v3 文档。
- 当前源码没有 i18n 框架，UI 为 Vue 3 / Vuetify 3 / Vue CLI；模板静态文案由上游 Vue compiler AST 解析。原始 UI 单测 48 套件/447 项通过；当前离线译文 AST 应用覆盖 341 个模板位置、331 个键，UI production build 通过（有上游 CSS/PWA/体积警告）。
- 项目 Python 测试 8 项通过；fork 的 Project checks 工作流通过；Actions YAML 与 shell 语法通过。
- 上游后端 Jest 131 套件/2501 项通过；`npm run build` 通过。Jest 需用 `--forceExit` 结束进程，因上游存在未关闭的异步句柄。尚未验证 Youdao 调用、GHCR 多架构发布或 NAS 运行。
- 已实际提取 331 个 9.6.0 静态模板文案键并离线填满翻译覆盖；术语表匹配 14 个键。翻译由模型生成，需人工复核；未来版本缓存未命中时才需要有道 Secrets，否则自动翻译门禁失败关闭。

## 下一步

1. 复核 `translations/zh-CN.json` 的模型初译；确认 AST 应用后的 UI build 通过。
2. 提交 9.6.0 翻译记忆与回填器修复到 fork，再手动派发 `Translate upstream release`，输入 `9.6.0` 与上述 commit；缓存命中时不会调用有道，门禁通过后自动派发镜像构建。
3. 为后续新文案配置 `YOUDAO_APP_KEY`、`YOUDAO_APP_SECRET`，以保持上游更新自动翻译。
4. 首次 GHCR 镜像和 Release 发布成功后，在测试环境验证，再由用户手动在绿联 NAS 部署。

## 检查与恢复

- Python 检查：`python3 -m unittest discover -s tests -v`
- 翻译提取：`node scripts/i18n.mjs extract --upstream /path/to/wud --output /tmp/wud-strings.json`
- 上游状态：`python3 scripts/check_upstream.py --current upstream.lock.json`
- 出错时保留现有 `upstream.lock.json` 和 GHCR 版本标签；回退部署时将 Compose 镜像版本改回此前成功的不可变 tag。
