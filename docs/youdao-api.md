# 有道智云文本翻译 API

实现基于有道官方[文本翻译 API 文档](https://ai.youdao.com/DOCSIRMA/html/trans/api/wbfy/index.html)，截至 2026-10-26 查阅。HTTPS endpoint：`https://openapi.youdao.com/api`；请求为 form POST，参数 `q/from/to/appKey/salt/sign/signType/curtime`。本工程使用 `en` → `zh-CHS` 与 v3 签名。

签名：`sha256(appKey + input + salt + curtime + appSecret)`，其中文本长度大于 20 字符时 `input = 前10字符 + 字符总数 + 后10字符`，否则 `input = q`。salt 每次使用 UUID，curtime 为 Unix UTC 秒。官方限制单次最多 5000 字符。脚本设置有限超时、指数退避重试，校验 `errorCode == 0` 与翻译结果；占位符不一致即失败。

缺失缓存且无密钥时失败关闭；完整缓存时离线可应用。翻译失败不会把半成品写入正式记忆库。每条请求间隔一秒，统计 API 请求数、提交字符数和待翻译字符数；实际费用依据有道账号套餐计费，不在代码中写死易过期单价。Secrets 不写日志。本工程只发送公开上游界面文案，不发送部署用户数据。术语表匹配项在发送前替换成保护标记，结果恢复为统一术语；无法保留标记时失败关闭。
