# wud-zh 接手文档

## 目标与边界

跟踪 WUD 已发布稳定版，为其 Vue UI 生成简体中文版本；自动化在 GitHub Actions 运行。工程已发布到 [Joker2021/wud-zh](https://github.com/Joker2021/wud-zh)，这是 `getwud/wud` 的 fork。上游 `ci.yml` 已在 fork 的 GitHub Actions 中禁用；本工程不会连接或修改用户 NAS。

## 当前版本与发布状态

- 当前维护分支：`main`；当前 HEAD 为 `ca6ebe418d552e7c746b5569d01b85641eee44c7`。漏派发补偿与安全续跑修复已纳入 main。本工作树含绿联 Compose bridge/MAC workaround、动态 UI 文案翻译和 revision 支持，均未提交或推送。
- 当前发布基线：WUD `9.6.0`，上游 commit `ae3c0827c020e62ba15b8df6edd5b04aa05e9e62`。官方 Release 页面标为 Latest，发布日期 2026-10-24。
- 首次中文镜像已发布：[WUD 9.6.0 简体中文版 Release](https://github.com/Joker2021/wud-zh/releases/tag/wud-9.6.0-zh.1)。GHCR `ghcr.io/joker2021/wud-zh` 的 `9.6.0-zh.1`、`stable`、`latest` 均已确认包含 `amd64` 与 `arm64`。
- [发布工作流](https://github.com/Joker2021/wud-zh/actions/runs/40221070914)通过上游测试、中文覆盖门禁、多架构构建、amd64 启动/认证/中文资源烟测及 GHCR 清单校验。
- 9.6.0 的 331 个静态文案键（236 条不同原文）由 Codex 离线初译并入库，首次没有请求有道；机器译文尚未人工复核。绿联 NAS 未连接、未部署或操作。
- 发布工作流可靠性修复已推送：`0d0a999` 支持同 digest 续跑并防止过期构建回退 `stable/latest`；`5e28aeff1552d025063df370667a26a67e6d039b` 修复 Buildx `Digest:` 多空格解析，Project checks [run 40224529737](https://github.com/Joker2021/wud-zh/actions/runs/40224529737) 通过。
- 修复前真实工作流 [run 40223095330](https://github.com/Joker2021/wud-zh/actions/runs/40223095330) 的上游测试/构建/覆盖门禁、amd64 smoke 和 OCI artifact 均成功；publish 在旧摘要解析器失败。它上传了 GHCR candidate `candidate-0d0a999e32fcd0debbd02d4fe1149c241b0ffc4f`，digest `sha256:1a6c8abe0135af2feb05feaf18535c1602ffc210e86cf5641d1b0546ebc6f14a`，含 amd64/arm64。正式版本 tag、stable/latest 和 Release 未改变；保留 candidate tag，不清理。
- 最近复查 `9.6.0-zh.1`、`stable`、`latest` digest 均为 `sha256:c772f6cbd78efab8b34fc766527ee1b892bce28eb88a279f2a40b8556dc48c52`，含 amd64/arm64。此前已有针对当前 lock 的成功发布 run；本次没有触发 Actions 或重跑 9.6.0。

## 关键目录

- `scripts/`：上游 Release 检测、Vue 静态文案与明确锚定的动态 UI 文案提取/应用、有道 API 翻译。
- `translations/`：简体中文覆盖、持久翻译记忆和术语表。
- `.github/workflows/`：Release 检查、翻译更新、构建与发布。
- `deploy/`：绿联 NAS Compose 示例。
- `deploy/docker-compose.ugreen.yml`：绿联 Compose 示例，绑定 `/volume1/docker/AppData/wud-zh/data` 到 `/store`，项目目录为 `/volume1/docker/AppData/wud-zh`，固定使用 9.6.0 镜像；管理员账号和密码为必填环境变量。容器加入专用 bridge network 并固定 MAC `02:00:00:00:12:12`。
- `docs/`：分析、架构、密钥设置、部署和排错。
- `.codex/skills/wud-zh/SKILL.md`：本项目稳定维护规则。

## 已检查与未检查

- 已核对官方 9.6.0 Release、源码标签、UI package manifest、Dockerfile、Actions 多架构配置、MIT 许可证和 Youdao 文本翻译 API v3 文档。
- 当前源码没有 i18n 框架，UI 为 Vue 3 / Vuetify 3 / Vue CLI；静态模板文案由上游 Vue compiler AST 解析，动态文案仅从 `scripts/i18n.mjs` 的精确源码锚点提取，锚点漂移会失败关闭。原始 UI 单测 48 套件/447 项通过；当前翻译覆盖门禁、UI production build 和 smoke 会检查所有动态翻译（含配置布尔值、退出/演示/复制提示）。
- 最新本地复核：动态 UI 词典/记忆扩展到 26 个动态源片段；展示层把已知 `admin`/`rw`/`ro` 角色映射为“管理员/读写/只读”，未知角色保留原值且权限判断仍用原始 role。run 40441215348 的 smoke 用宿主机 chunk 文件名读取镜像，因 Docker 内重建的 JS chunk hash 不同而漏检配置抽屉文案；已改为从容器 `/home/node/app/ui/js` 枚举并检查实际服务资源的 JavaScript Content-Type。修复尚未经新的 Actions run 验证。当前项目 Python 测试、Vue production build、workflow YAML/run 脚本语法及 `git diff --check` 已运行。未运行 Actions/GHCR/绿联 NAS。
- 漏派发恢复：translate 请求 check-upstream 协调发布；协调器按 exact run-name `Build WUD <version> (<commit>) zh.<revision>` 查运行记录，自动 revision 1，失败最多 3 次，queued/in_progress 防重复。旧格式 run 迁移时，无新格式匹配记录但版本 Release 已存在则视为已发布；若精确匹配的新 run 失败，即使 Release 已存在仍重试。Release API 状态不确定时 fail closed。
- `build-release.yml` 现在要求 workflow_dispatch 提供与 lock 一致的 `version` 和 `commit`，并支持正整数 revision（默认 `1`）；run-name 记录三者，reconciler 不拉取完整 Git 历史。自动协调固定使用 revision `1`，发布标签为 `${VERSION}-zh.${REVISION}`，项目 revision OCI label 用于安全续跑校验。`9.6.0-zh.2` 尚未发布；UGREEN Compose 仍指向已发布的 `.1`。
- 锁定的上游 9.6.0 不支持 `WUD_AUTH_SESSION_SECRET`；该变量会被误识别为未知的 `session` auth provider。绿联 Compose 改用固定 bridge MAC `02:00:00:00:12:12` 供 `getmac` 回退读取，端口为 `12712:3000`。这是配置 workaround，尚未在真实绿联 NAS 验证；未修改 backend 或上游构建工作流。
- 上游后端 Jest 131 套件/2501 项通过；`npm run build` 通过。Jest 需用 `--forceExit` 结束进程，因上游存在未关闭的异步句柄。GHCR 发布及两个架构的 manifest 已通过远端复核；smoke runtime 只在 amd64 runner 执行。
- 已实际提取并离线填满 9.6.0 翻译覆盖；动态 UI 字符串包含导航配置项、用户状态、侧栏标题、配置计数/布尔值、退出失败提示、演示用户切换提示及复制成功/失败 toast。精确锚点不匹配时提取失败关闭；已知三种角色标签映射为中文，未知角色、用户名、配置值及错误详情等运行时字段保持原样。首次翻译没有请求有道；既有译文仍需人工复核，未来版本缓存未命中时才需要有道 Secrets，否则自动翻译门禁失败关闭。

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
