# 构建与发布架构

1. `check-upstream.yml` 每 6 小时查询 GitHub 当前正式 stable Release，并解析精确 tag commit。新版本时仅触发翻译工作流。
2. `translate.yml` 下载固定 SHA 源码，使用上游 UI 已有 Vue compiler 提取静态模板文案。脚本只发送提取的 UI 文案给有道。已有 `translations/memory.json` 条目直接复用，新增译文在占位符校验后原子写入缓存。
3. 工作流先在原始英文源码上运行上游 UI Jest（当前用例会断言英文 UI 文案），再应用中文覆盖并运行生产构建。通过后将上游版本锁和翻译缓存提交到 fork 的 `main`，并显式派发构建工作流；解析、翻译或测试失败时停止。
4. `build-release.yml` 从 lock SHA 取源码，再在原始英文源码上运行 UI/Jest 和 backend 测试，应用静态译文并构建 UI，最后用上游 Dockerfile 生成 amd64/arm64 候选 manifest。
5. Actions 在 amd64 runner 启动候选容器，检查健康端点与静态页面；检查 OCI manifest 同时包含目标架构。全部门禁成功后才把不可变版本 tag、`stable` 和 `latest` 指向同一候选 digest，并创建 GitHub Release。

上游代码只在无翻译密钥的安装/构建/测试步骤执行。Youdao Secrets 只进入项目翻译脚本进程，不传给 npm、Docker BuildKit 或上游脚本。工作流由 schedule、workflow_dispatch 和翻译门禁成功后的显式构建派发驱动；外部 PR 代码不接触 Secrets。

Fork 继承的上游 `ci.yml` 已在 GitHub Actions 中禁用，避免触发上游的 Docker 镜像发布、截图回写或文档站点部署。`build-release.yml` 仅响应手动派发或通过翻译测试后的显式派发。

翻译和兼容性门禁通过后，workflow bot 自动写入 fork 的 `main` 并派发镜像构建；GitHub Actions 的 `GITHUB_TOKEN` 推送不会依赖 push 事件触发后续工作流。镜像只有在构建、manifest 校验和 amd64 启动/认证/中文资源烟测通过后才发布。

翻译键由相对文件、Vue 元素/属性上下文和源文生成 SHA-256。翻译记忆不会依赖 Actions 临时缓存。若文本结构移动到脚本、后端响应或动态表达式，提取覆盖率门禁停止发布，由维护者调整提取器并审阅。

**验证边界：** 多架构构建会验证构建完成和 manifest 平台；运行时 smoke test 只在 amd64 runner 上执行。认证完整流程、镜像更新结果及 ARM64 原生运行仍需真实环境验证。
