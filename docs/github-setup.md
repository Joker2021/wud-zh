# GitHub Actions 与 Secrets 设置

1. 在 GitHub fork `getwud/wud`，将本项目文件加入该 fork 的默认分支（`main`）。Actions、Secrets 和 GHCR 镜像均归 fork 所有者。不要把 Youdao key/secret 放进文件、`.env`、Issue 或 commit。
2. 在仓库 **Settings → Secrets and variables → Actions** 新建：
   - `YOUDAO_APP_KEY`：有道智云应用 ID。
   - `YOUDAO_APP_SECRET`：有道智云应用密钥。
3. 建立仓库变量 `WUD_IMAGE`，值为 `ghcr.io/<owner>/wud-zh`。GHCR package 由本仓库 `GITHUB_TOKEN` 发布。
4. 在仓库 Actions 设置中启用 workflows，并允许工作流写入仓库和发布 packages；工作流按 job 配置最小权限，无需长期 PAT。
5. 首次建立翻译库时，在 Actions 手动运行 `Translate upstream release`，版本输入 `9.6.0`、commit 输入 `ae3c0827c020e62ba15b8df6edd5b04aa05e9e62`。它核对官方最新稳定版，提取、翻译并测试；通过后自动提交版本锁和翻译记忆到 `main`，再派发 `Build and publish WUD Chinese image`。
6. `Check upstream` 每 6 小时查询官方稳定版。有新版本时自动派发翻译工作流；翻译或兼容性检查失败会停止，不更新 `main` 或现有镜像。构建及烟测通过后才发布不可变版本 tag、`stable`、`latest` 和 GitHub Release。无需人工合并 PR。

有道按账号套餐计量和收费。首次更新可能会翻译许多缓存缺失的 UI 静态文案；先确认翻译规模再配置 Secret。API key/secret 绝不传给上游 `npm ci`、Docker build 或外部 Pull Request 工作流。

GitHub 403/API 限流时由 `GITHUB_TOKEN` 提供仓库 API 认证；若失败，检查 workflow permissions 和 GitHub 状态，不要退回抓取 `latest` 镜像标签来猜版本。
