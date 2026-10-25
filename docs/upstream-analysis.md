# WUD 上游源码分析

## 核对基线

本次以 WUD 9.6.0 为正式 Release 基线，Release 页面标为 Latest，发布日期为 2026-10-24，commit 为 `ae3c0827c020e62ba15b8df6edd5b04aa05e9e62`。我第一次检索时 Releases 索引和 Changelog 缓存尚停留在 9.5.0；随后打开官方 9.6.0 Release 页面确认它已正式发布。Release 检查工作流调用 GitHub `/releases/latest`，跳过 draft、prerelease 和非 SemVer 标签，再递归解析 tag object 到不可变 commit SHA。

来源：[WUD 9.6.0 官方 Release](https://github.com/getwud/wud/releases/tag/9.6.0)、[官方 Releases](https://github.com/getwud/wud/releases)、[9.6.0 源码](https://github.com/getwud/wud/tree/9.6.0)。GitHub REST API 在当前环境响应 403；官方 Release 页面提供了版本、发布时间和 commit SHA。

## 技术栈与构建

- 前端：Vue 3、Vuetify 3、Vue Router 4、TypeScript；Vue CLI 5 构建。版本和依赖范围在 `ui/package.json`，锁定依赖在 `ui/package-lock.json`。
- 后端：Node.js/TypeScript 应用，`app/package.json` 定义 Jest 测试。UI 自带 Jest 单测。官方仓库另有 E2E 和 CI workflow。
- 前端位于 `ui/src/`，包括 views、components、router、services、plugins 等。可见英文文本主要在 Vue SFC template 中直接书写，部分动态错误消息在组件脚本中生成。
- 官方 Dockerfile 分别构建 `app/` 和 `ui/`，再将 `dist` 和 UI 静态文件装入 Node 24 Alpine runtime。项目直接用固定 commit 中的 Dockerfile，不重写后端构建。
- 官方 CI 声明 `linux/arm64/v8,linux/amd64`；本工程使用 `linux/arm64` 与 `linux/amd64` manifest。
- 上游许可证为 MIT；构建保留原 LICENSE、copyright 和来源信息，并在镜像标签及 Release Notes 记录上游版本/commit。

## i18n 与文案路径

在基线 UI 源码和依赖中未发现 `vue-i18n` 或官方语言包/切换机制。模板中的普通文本和常见静态文案属性适合用上游 Vue compiler AST 安全定位，不需要字符串全局替换。工程只处理模板 text 节点以及 `placeholder`、`title`、`aria-label`、`alt`、`label` 静态属性；保留绑定表达式、方法、组件/字段名、URL 和 API 路径。

Vue 插值表达式通常与相邻 text 节点分开；译文仍对 `{name}`、`{{count}}`、`${variable}` 和 `%s` 作占位符一致性校验。用户数据和 Docker 标识不进入提取清单。由于没有原生 locale 架构，当前使用默认简体中文静态资源；未实现英语/中文运行时切换。脚本动态消息、后端错误内容也不在自动覆盖内，不能宣称覆盖全部用户可见英文。

## 认证、存储和 Docker 行为

WUD v9 强制管理员认证。官方启动参数为 `WUD_AUTH_ADMIN_USER` 与 `WUD_AUTH_ADMIN_PASSWORD`。SQLite 状态默认存储在 `/store/wud.sqlite`，部署文件将 `/store` 挂载为命名卷。

本示例只配置本地 Docker watcher，不配置通知或更新 Trigger；用户手动选择升级 NAS 上 WUD 镜像。Docker socket 具备高权限，即使以 `:ro` 挂载也无法限制 Docker API 操作。

## 当前证据与缺口

- 已核对 9.6.0 源码结构与 package 清单、Release 页面、commit SHA、Docker 构建规则和 v9 管理员配置。CI 将从 9.6.0 固定 commit 重新获取并验证。
- 上游 UI 单测通过（48 suites / 447 tests）；使用测试占位译文的 AST 应用后，Vue UI production build 通过。该假译文只用于临时源码构建验证，没有写入项目翻译库。
- 上游后端 Jest 131 套件/2501 项通过，TypeScript `npm run build` 通过；测试运行需 `--forceExit` 处理上游未关闭的异步句柄。Docker 启动、认证请求、容器镜像更新集成测试和真实 NAS 测试仍未完成。
- 已使用 9.6.0 上游编译器真实提取到 331 个不同上下文的静态模板文案键；术语表直接覆盖 14 个键，另有 317 个键需要 Youdao API 翻译。目前无 Youdao 凭据，translation cache 为空，也没有完整人工审校译文。
- 项目 Python 测试 8 项、上游 UI 单测 48 套件/447 项、上游后端测试 131 套件/2501 项，以及 UI production build 和后端 TypeScript build 均通过；多架构镜像流程尚未通过本地执行。
- 未配置 GitHub 仓库、Secrets、GHCR 权限和 NAS，因此自动更新/发布链路尚未实际端到端执行。
- 官方文档声明架构，不等于本项目镜像已构建验证。CI 需检查多架构 manifest；容器运行烟测在 amd64 runner 上完成，ARM64 运行时还需设备或原生 runner 验证。
