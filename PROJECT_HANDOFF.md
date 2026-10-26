# wud-zh 接手文档

## 目标与边界

跟踪 WUD 已发布稳定版，为其 Vue UI 生成简体中文版本；自动化在 GitHub Actions 运行。工程已发布到 [Joker2021/wud-zh](https://github.com/Joker2021/wud-zh)，这是 `getwud/wud` 的 fork。上游 `ci.yml` 已在 fork 的 GitHub Actions 中禁用；本工程不会连接或修改用户 NAS。

## 当前版本与发布状态

- 当前维护分支：`main`；发布流程摘要解析修复已推送。当前工作树新增了漏派发补偿与安全续跑改动，尚未推送。
- 当前发布基线：WUD `9.6.0`，上游 commit `ae3c0827c020e62ba15b8df6edd5b04aa05e9e62`。官方 Release 页面标为 Latest，发布日期 2026-10-24。
- 首次中文镜像已发布：[WUD 9.6.0 简体中文版 Release](https://github.com/Joker2021/wud-zh/releases/tag/wud-9.6.0-zh.1)。GHCR `ghcr.io/joker2021/wud-zh` 的 `9.6.0-zh.1`、`stable`、`latest` 均已确认包含 `amd64` 与 `arm64`。
- [发布工作流](https://github.com/Joker2021/wud-zh/actions/runs/40221070914)通过上游测试、中文覆盖门禁、多架构构建、amd64 启动/认证/中文资源烟测及 GHCR 清单校验。
- 9.6.0 的 331 个静态文案键（236 条不同原文）由 Codex 离线初译并入库，首次没有请求有道；机器译文尚未人工复核。NAS 未连接、未部署。
- 发布工作流可靠性修复已推送：`0d0a999` 支持同 digest 续跑并防止过期构建回退 `stable/latest`；`5e28aeff1552d025063df370667a26a67e6d039b` 修复 Buildx `Digest:` 多空格解析，Project checks [run 40224529737](https://github.com/Joker2021/wud-zh/actions/runs/40224529737) 通过。
- 修复前真实工作流 [run 40223095330](https://github.com/Joker2021/wud-zh/actions/runs/40223095330) 的上游测试/构建/覆盖门禁、amd64 smoke 和 OCI artifact 均成功；publish 在旧摘要解析器失败。它上传了 GHCR candidate `candidate-0d0a999e32fcd0debbd02d4fe1149c241b0ffc4f`，digest `sha256:1a6c8abe0135af2feb05feaf18535c1602ffc210e86cf5641d1b0546ebc6f14a`，含 amd64/arm64。正式版本 tag、stable/latest 和 Release 未改变；保留 candidate tag，不清理。
- 最近复查 `9.6.0-zh.1`、`stable`、`latest` digest 均为 `sha256:c772f6cbd78efab8b34fc766527ee1b892bce28eb88a279f2a40b8556dc48c52`，含 amd64/arm64。此前已有针对当前 lock 的成功发布 run；本次没有触发 Actions 或重跑 9.6.0。

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
- 本次新增漏派发恢复：translate 改为请求 check-upstream 协调发布；协调器以 exact run-name `Build WUD <version> (<commit>)` 查运行记录，失败最多 3 次，queued/in_progress 防重复。旧格式 run 迁移时，如果无 exact-name 记录但版本 Release 已存在则视为已发布；如果新格式 exact-name run 失败，即使 Release 已存在仍重试。Release API 状态不确定时 fail closed。
- `build-release.yml` 现在要求 workflow_dispatch 提供 `version` 和 `commit`，run-name 记录二者，validator 校验与 lock 完全一致。reconciler 不拉取完整 Git 历史。11 个决策测试和工作流静态检查通过；新 reconciliation、现有 immutable tag 双架构 labels/manifest 续跑尚未在 Actions/GHCR 实际验证。
- 上游后端 Jest 131 套件/2501 项通过；`npm run build` 通过。Jest 需用 `--forceExit` 结束进程，因上游存在未关闭的异步句柄。GHCR 发布及两个架构的 manifest 已通过远端复核；smoke runtime 只在 amd64 runner 执行。
- 已实际提取 331 个 9.6.0 静态模板文案键并离线填满翻译覆盖；术语表匹配 14 个键。翻译由模型生成，需人工复核；未来版本缓存未命中时才需要有道 Secrets，否则自动翻译门禁失败关闭。

## 下一步

1. 等待上游发布新版本；下一次 6 小时检查会在翻译/锁文件推送后的 dispatch 丢失时补偿。build dispatch 只接受版本和 commit 与当前 lock 一致的输入；新版本首次成功发布前最多自动尝试 3 次。
2. 已存在的 immutable tag 若与重建 candidate digest 不同，自动流程只会在核对 version/revision labels 及 amd64/arm64 manifests 后复用旧 tag；stable/latest 从 immutable tag 提升。未匹配时停止并要求维护者检查。
3. 人工抽查 `translations/zh-CN.json` 中的机器初译，后续提交修订。
4. 用户可先在测试环境验证 `ghcr.io/joker2021/wud-zh:9.6.0-zh.1`，再按 NAS 指南手动部署；本任务没有操作 NAS。

## 检查与恢复

- Python 检查：`python3 -m unittest discover -s tests -v`
- 翻译提取：`node scripts/i18n.mjs extract --upstream /path/to/wud --output /tmp/wud-strings.json`
- 上游状态：`python3 scripts/check_upstream.py --current upstream.lock.json`
- 出错时保留现有 `upstream.lock.json` 和 GHCR 版本标签；回退部署时将 Compose 镜像版本改回此前成功的不可变 tag。
- 发布工作流本地检查：解析 `.github/workflows/build-release.yml`，对每个 `run` 脚本执行 `bash -n`，再运行 `git diff --check`。
