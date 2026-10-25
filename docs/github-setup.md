# GitHub Actions 与 Secrets 设置

1. 在 GitHub fork `getwud/wud`，将本项目文件加入该 fork 的默认分支（`main`）。Actions、Secrets 和 GHCR 镜像均归 fork 所有者。不要把 Youdao key/secret 放进文件、`.env`、Issue 或 commit。
2. 在仓库 **Settings → Secrets and variables → Actions** 新建：
   - `YOUDAO_APP_KEY`：有道智云应用 ID。
   - `YOUDAO_APP_SECRET`：有道智云应用密钥。
3. 建立仓库变量 `WUD_IMAGE`，值使用小写地址，例如 `ghcr.io/joker2021/wud-zh`。GHCR package 由本仓库 `GITHUB_TOKEN` 发布。
4. 在仓库 Actions 设置中启用 workflows，并允许工作流写入仓库和发布 packages；工作流按 job 配置最小权限，无需长期 PAT。
5. 首次启动时，在 Actions 手动运行 `Translate upstream release`，版本输入 `9.6.0`、commit 输入 `ae3c0827c020e62ba15b8df6edd5b04aa05e9e62`。当前初始文案已离线写入翻译记忆，因此首次运行可不配置有道 Secrets；它会复用缓存、核对版本、运行测试并派发构建。后续版本遇到未缓存文案时，需配置两项有道 Secrets 才能继续。
6. `Check upstream` 每 6 小时查询官方稳定版。有新版本时自动派发翻译工作流；翻译或兼容性检查失败会停止，不更新 `main` 或现有镜像。构建及烟测通过后才发布不可变版本 tag、`stable`、`latest` 和 GitHub Release。无需人工合并 PR。

有道按账号套餐计量和收费。未来上游新增文案会按缓存缺失量调用 API；API key/secret 绝不传给上游 `npm ci`、Docker build 或外部 Pull Request 工作流。

GitHub 403/API 限流时由 `GITHUB_TOKEN` 提供仓库 API 认证；若失败，检查 workflow permissions 和 GitHub 状态，不要退回抓取 `latest` 镜像标签来猜版本。
