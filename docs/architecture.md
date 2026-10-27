# 构建与发布架构

1. `check-upstream.yml` 每 6 小时查询 GitHub 当前正式 stable Release，并解析精确 tag commit。发现新版本时触发翻译；上游已与 lock 一致时，按 `Build WUD <version> (<commit>) zh.1` 精确匹配构建 run。排队/运行中构建不重复派发，失败最多自动尝试 3 次；旧格式 run 迁移期间以已存在的版本 Release 作为完成基线。无法确认 run 或 Release API 状态时停止自动派发并给出 warning。
2. `translate.yml` 下载固定 SHA 源码，使用上游 UI 的 Vue compiler 提取静态模板文案，并提取 `scripts/i18n.mjs` 中列出的、有精确源码锚点的动态 UI 字符串（导航/用户状态、退出登录与演示切换提示、配置计数/布尔值及复制 toast）。已知 `admin`/`rw`/`ro` 仅在当前用户角色展示处映射为“管理员/读写/只读”，权限逻辑仍使用原始 role，未知角色保持原值。锚点缺失或重复时失败关闭；插值的用户名、配置键/值和错误详情保持运行时原值，只翻译固定文案。脚本只发送提取的 UI 文案给有道；已有 `translations/memory.json` 条目直接复用，新增译文在占位符校验后原子写入缓存。
3. 工作流先在原始英文源码上运行上游 UI Jest（当前用例会断言英文 UI 文案），再应用中文覆盖并运行生产构建。通过后将上游版本锁和翻译缓存提交到 fork 的 `main`，并请求上游检查工作流协调镜像发布；若请求失败，后续 6 小时检查会补偿。解析、翻译或测试失败时停止。
4. `build-release.yml` 从 lock SHA 取源码，再在原始英文源码上运行 UI/Jest 和 backend 测试，应用静态与精确锚定的动态译文并构建 UI，最后用上游 Dockerfile 生成 amd64/arm64 候选 manifest。
5. Actions 在 amd64 runner 启动候选容器，检查健康端点与静态页面及动态中文文案；检查 OCI manifest 同时包含目标架构。若版本 tag 不存在，创建不可变 tag 并核对 digest；若 tag 已存在且候选 digest 不同，仅在两架构 manifest、上游版本/commit labels 和项目 revision label 均匹配时复用它。`stable` 和 `latest` 始终从不可变版本 tag 提升，并在 GitHub Release 创建或续跑后检查 main 锁。

上游代码只在无翻译密钥的安装/构建/测试步骤执行。Youdao Secrets 只进入项目翻译脚本进程，不传给 npm、Docker BuildKit 或上游脚本。工作流由 schedule 和 workflow_dispatch 驱动；外部 PR 代码不接触 Secrets。

Fork 继承的上游 `ci.yml` 已在 GitHub Actions 中禁用，避免触发上游的 Docker 镜像发布、截图回写或文档站点部署。`build-release.yml` 仅响应手动派发或检查/协调工作流的显式派发。翻译记忆已覆盖当前版本时，工作流跳过无变化提交但仍请求检查/协调工作流。

`build-release.yml` 的 `workflow_dispatch` 必须携带与 `upstream.lock.json` 一致的 `version` 和 `commit`，并接受正整数 `revision`（默认 `1`）。run-name 包含版本、上游 commit 和 revision；发布标签为 `${VERSION}-zh.${REVISION}`。自动协调固定传入 revision `1`，项目 revision OCI label 用于安全续跑核验。协调流程按完整 run-name 去重，不拉取完整 Git 历史。

翻译和兼容性门禁通过后，workflow bot 自动写入 fork 的 `main` 并请求检查/协调工作流；GitHub Actions 的 `GITHUB_TOKEN` 推送不会依赖 push 事件触发后续工作流。镜像只有在构建、manifest 校验和 amd64 启动/认证/中文资源烟测通过后才发布。

翻译键由相对文件、Vue 元素/属性上下文和源文生成 SHA-256。翻译记忆不会依赖 Actions 临时缓存。静态 AST 提取之外，仅允许提取脚本明列的精确动态文本锚点；锚点变更会停止发布，由维护者调整提取器并审阅。配置布尔状态、退出登录失败提示、演示账号切换提示和复制成功/失败 toast 已纳入动态文案；仅已知角色枚举在显示层映射，未知角色、用户名、配置值和错误详情等运行时字段保留原样。

**验证边界：** 多架构构建会验证构建完成和 manifest 平台；运行时 smoke test 只在 amd64 runner 上执行。认证完整流程、镜像更新结果及 ARM64 原生运行仍需真实环境验证。
