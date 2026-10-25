# wud-zh 接手文档

## 目标与边界

跟踪 WUD 已发布稳定版，为其 Vue UI 生成简体中文版本；自动化在 GitHub Actions 运行。工程已发布到 [Joker2021/wud-zh](https://github.com/Joker2021/wud-zh)，这是 `getwud/wud` 的 fork。上游 `ci.yml` 已在 fork 的 GitHub Actions 中禁用；本工程不会连接或修改用户 NAS。

## 当前版本与发布状态

- 当前维护分支：`main`；HEAD 为 `5e28aeff1552d025063df370667a26a67e6d039b`。发布流程重试与摘要解析修复已推送。
- 当前发布基线：WUD `9.6.0`，上游 commit `ae3c0827c020e62ba15b8df6edd5b04aa05e9e62`。官方 Release 页面标为 Latest，发布日期 2026-10-24。
- 首次中文镜像已发布：[WUD 9.6.0 简体中文版 Release](https://github.com/Joker2021/wud-zh/releases/tag/wud-9.6.0-zh.1)。GHCR `ghcr.io/joker2021/wud-zh` 的 `9.6.0-zh.1`、`stable`、`latest` 均已确认包含 `amd64` 与 `arm64`。
- [发布工作流](https://github.com/Joker2021/wud-zh/actions/runs/40221070914)通过上游测试、中文覆盖门禁、多架构构建、amd64 启动/认证/中文资源烟测及 GHCR 清单校验。
- 9.6.0 的 331 个静态文案键（236 条不同原文）由 Codex 离线初译并入库，首次没有请求有道；机器译文尚未人工复核。NAS 未连接、未部署。
- 发布工作流可靠性修复已提交：`0d0a999` 支持相同版本 digest 续跑并保护 `stable/latest` 不被过期构建回退；`5e28aeff1552d025063df370667a26a67e6d039b` 修复 Buildx `Digest:` 多空格解析，并在发布脚本中加入有效/无效摘要自检。后者的 YAML、6 个内嵌 shell 语法、自检和 Project checks 均通过。
- 对修复前版本执行的真实工作流 [run 40223095330](https://github.com/Joker2021/wud-zh/actions/runs/40223095330) 中，上游测试、构建、覆盖门禁、amd64 smoke 和 OCI artifact 成功；publish 在旧摘要解析器处失败。它已将 `candidate-0d0a999e32fcd0debbd02d4fe1149c241b0ffc4f` 上传至 GHCR，摘要 `sha256:1a6c8abe0135af2feb05feaf18535c1602ffc210e86cf5641d1b0546ebc6f14a`，含 amd64/arm64。该次未改正式版本 tag、`stable`、`latest` 或 GitHub Release。
- 修复后的 Project checks [run 40224529737](https://github.com/Joker2021/wud-zh/actions/runs/40224529737) 通过；修复后的 publish job 尚未实际重跑。最近复查 `9.6.0-zh.1`、`stable`、`latest` digest 均仍为 `sha256:c772f6cbd78efab8b34fc766527ee1b892bce28eb88a279f2a40b8556dc48c52`，清单含 amd64/arm64。候选重建 digest 与不可变版本 tag 不同，因此不要重跑 9.6.0 发布；等待新的上游版本后再走完整发布链路。

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
- 上游后端 Jest 131 套件/2501 项通过；`npm run build` 通过。Jest 需用 `--forceExit` 结束进程，因上游存在未关闭的异步句柄。GHCR 发布及两个架构的 manifest 已通过远端复核；smoke runtime 只在 amd64 runner 执行。
- 已实际提取 331 个 9.6.0 静态模板文案键并离线填满翻译覆盖；术语表匹配 14 个键。翻译由模型生成，需人工复核；未来版本缓存未命中时才需要有道 Secrets，否则自动翻译门禁失败关闭。

## 下一步

1. 等待上游发布新版本，再确认锁文件和工作流构建/发布行为；不要用同一 9.6.0 重建覆盖不可变 tag。
2. 人工抽查 `translations/zh-CN.json` 中的机器初译，后续提交修订。
3. 用户可先在测试环境验证 `ghcr.io/joker2021/wud-zh:9.6.0-zh.1`，再按 NAS 指南手动部署；本任务没有操作 NAS。

## 检查与恢复

- Python 检查：`python3 -m unittest discover -s tests -v`
- 翻译提取：`node scripts/i18n.mjs extract --upstream /path/to/wud --output /tmp/wud-strings.json`
- 上游状态：`python3 scripts/check_upstream.py --current upstream.lock.json`
- 出错时保留现有 `upstream.lock.json` 和 GHCR 版本标签；回退部署时将 Compose 镜像版本改回此前成功的不可变 tag。
- 发布工作流本地检查：解析 `.github/workflows/build-release.yml`，对每个 `run` 脚本执行 `bash -n`，再运行 `git diff --check`。
