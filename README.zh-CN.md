# Awesome AI API 中转站 [![Awesome](https://awesome.re/badge.svg)](https://awesome.re)

> 一份**持续维护**的 AI API 中转站 / 代理（"中转站"）、全球 LLM 网关，
> 以及评估工具的清单 —— 基于证据，讲清楚这个市场为什么存在、风险在哪。

**语言：** [English](README.md) · [繁體中文](README.zh-TW.md) · 简体中文

最后审阅：**2026-05-16** · 维护者 [@howardpen9](https://github.com/howardpen9) ·
欢迎贡献 —— 见 [CONTRIBUTING.md](CONTRIBUTING.md)

---

## 目录

- [什么是 API 中转站](#什么是-api-中转站)
- [为什么会出现（全球视角）](#为什么会出现全球视角)
- [中国 / 亚洲中转站](#中国--亚洲中转站)
- [海外网关与聚合平台](#海外网关与聚合平台)
- [对比与监控工具](#对比与监控工具)
- [如何安全地挑选](#如何安全地挑选)
- [风险（务必阅读）](#风险务必阅读)
- [市场背景](#市场背景)
- [常见问题 FAQ](#常见问题-faq)
- [参与贡献](#参与贡献)

---

## 什么是 API 中转站

> **API 中转站（AI API Relay）是一个转发端点，夹在你的代码和官方 LLM API
> 之间。** 你把 `base_url` 改成中转站、用它给的 key，就能调用 OpenAI / Claude /
> Gemini 等几十种模型——一个 key、人民币付款（支付宝/微信）、低延迟，通常比官方
> 便宜 30–90%。

**API 中转站**（也叫 "AI API 代理 / Relay"）是一个中间转发端点。你不直接调
OpenAI、Anthropic、Google 等官方 API，而是把 `base_url` 改成中转站地址、用它
给的 Key。中转站帮你转发到官方后端再把结果回传 —— 通常**完全兼容 OpenAI 格式**，
代码几乎不用改。

一个 Key 打通几十到上百种跨厂商模型。

它和**镜像站**不同：镜像站是给一般人用的代理版聊天网页；中转站是给
**开发者和程序**用的接口。

## 为什么会出现（全球视角）

中转站不是中国独有，而是**访问封锁 + 支付障碍**这两个痛点共同的产物：

| 地区 | 访问障碍 | 支付障碍 |
|---|---|---|
| 中国 | 跨境延迟高、部分 API 不可用 | 需国外信用卡；中转站收支付宝/微信 |
| 俄罗斯 / 白俄 / 伊朗 | OpenAI 硬封锁（连 VPN 都被识别） | 受制裁银行卡（如伊朗 Shetab）被拒 |
| 亚太含台湾 | 通常可连 | 信用卡被拒、额度限制、账单麻烦 |
| 受制裁 / 受限市场 | 注册被拒 | 没有可用的支付通道 |

同样的需求长出不同生态：俄罗斯靠 IP 代理 + 国产替代（如 GigaChat），中国则演化
出完整的**中转站零售业**。全球"干净版"是官方授权聚合平台（见下方 OpenRouter）
—— 证明"统一调用多厂商模型"是真实增长的市场，而非小众绕路。

## 中国 / 亚洲中转站

> 状态：`active` = 可独立访问；`unverified` = 社区来源，未独立确认。
> 价格变动极快，请以官网为准。数据生成自 [`data/providers.yaml`](data/providers.yaml)。

| 中转站 | 类型 | 支付 | 状态 | 备注 |
|---|---|---|---|---|
| [云雾 API (YUNWU)](https://yunwu.ai) | mixed | 支付宝/微信 | active | 主打高速稳定；社区常列为头部站。 |
| [柏拉图 AI (bltcy)](https://api.bltcy.ai) | mixed | 支付宝/微信 | active | Azure 通道；主打最低价。 |
| [No.1-API](https://api.rcouyi.com) | aggregator | 支付宝/微信 | active | 一站式聚合 + 中转平台。 |
| [UiUiAPI](https://uiuiapi.com) | official-relay | 支付宝/微信 | active | 宣称官方渠道 + 官方倍率；约便宜 49%（宣称），300+ 模型。 |
| [DMXAPI](https://dmxapi.cn) | mixed | 支付宝/微信 | unverified | 社区收录；官网未独立核实。 |
| [MKEAI](https://mkeai.com) | mixed | 支付宝/微信 | unverified | 社区论坛 + 中转混合；主推 DeepSeek。 |
| [GPTGOD](https://gptgod.online) | reverse | 支付宝 | unverified | 逆向；便宜，稳定性无保证。 |
| [CloseAI](https://www.closeai-asia.com) | official-relay | 支付宝/微信/对公 | active | 自称亚洲最大企业级中转。 |

> **收录 ≠ 推荐。** 收录是为了记录市场。打款或传数据前请先走
> [评估清单](docs/evaluation.md)。

## 海外网关与聚合平台

| 服务 | 类型 | 支付 | 备注 |
|---|---|---|---|
| [OpenRouter](https://openrouter.ai) | aggregator | 卡/加密货币 | 官方授权路由，加价约 5%；400+ 模型、60+ 供应商。ARR 据报约 $5M（2025-05）→ 约 $50M（2026 初）。 |
| [LiteLLM](https://litellm.ai) | gateway-oss | — | 开源网关（100+ 供应商）+ 企业版。自托管，自带 Key。 |
| [Helicone](https://helicone.ai) | observability | — | LLM 可观测性网关；日志/成本分析。 |
| [AIMLAPI](https://aimlapi.com) | aggregator | 卡/加密货币 | 400+ 模型，$20 起预付；支持加密货币暗示绕支付障碍。 |

## 对比与监控工具

| 工具 | 备注 |
|---|---|
| [中转站竞技场 (AI API PK)](https://www.aiapipk.com) | 约 40 家站点的 OpenAI / 逆向 / Claude / DeepSeek 报价墙。 |
| [awesome-ai-proxy (mn-api)](https://github.com/mn-api/awesome-ai-proxy) | 最早的清单（约 31 家）。**2026 年起已停更** —— 本仓库延续这一工作。 |

## 如何安全地挑选

完整框架见 **[docs/evaluation.md](docs/evaluation.md)**。速览：

1. **先看通道类型** —— `official-relay` > `mixed` > `aggregator` > `reverse`。
2. **做 canary 测试** —— 用已知难题，官方 vs 中转，每周比对，识别偷偷降智。
3. **小额充值** —— 中转站基本都是预付，绝不大额预存。
4. **按场景匹配** —— 敏感/合规数据走官方 API 或自托管 `gateway-oss`，绝不用 `reverse`。

## 风险（务必阅读）

市场基本无监管。来自公开研究：

- 一项对 **28 个中转站**的测试发现 **45.83% 的 API 端点返回的模型与请求不符**
  （医疗任务性能差距达 47%）。
- 对 **428 个站点**的审计发现 **9 个注入恶意代码**、**1 个直接盗取资金**。
- 调研 17 家头部站，**15 家无注册公司**。

完整说明与来源见 **[docs/risks.md](docs/risks.md)**。

## 市场背景

- 最早的社区清单（[mn-api/awesome-ai-proxy](https://github.com/mn-api/awesome-ai-proxy)）
  收录约 31 家后停更；aiapipk.com 等聚合约 40 家 —— 这只是冰山一角。
- "干净版"全球对应物 OpenRouter，据报不到一年 ARR 增长约 10 倍（约 $5M → 约
  $50M），月处理万亿级 token —— 强力证明"统一多厂商访问"是可持续市场。
- 结论：中转站是**封锁 + 支付障碍的全球性回应**，中国生态最深，因为两个痛点
  在那里最集中。

## 常见问题 FAQ

### API 中转站是什么？

API 中转站是夹在你的代码和官方 LLM API（OpenAI、Anthropic、Google）之间的转发
端点。你把 `base_url` 改成中转站、用它给的 key，它帮你转发到官方后端再回传结
果，通常完全兼容 OpenAI 格式。一个 key 就能用几十到上百种跨厂商模型。

### API 中转站安全吗？会被盗 key 或偷 prompt 吗？

把每个中转站都当成不可信的中间人。它能看到你所有的 prompt、响应和传出去的数
据——恶意运营者可以记录、篡改或外泄。对 428 个站点的审计发现 9 个注入恶意代
码、1 个直接盗资金。绝不要通过中转站传密钥或受监管数据；敏感场景请用官方 API
或自托管网关。

### API 中转站为什么比官方便宜这么多？

三个原因：上游批发价、混合通道（如 Azure 额度）、以及最便宜那一档的"逆向"（从
厂商网页版反向工程）。价格只有官方 1/10 到 1/50 的，通常代表逆向通道或偷偷降
智，不是真的捡到便宜。

### 官转、混合、逆向差在哪？哪个能用在 production？

`官转（official-relay）`转发真正的官方 key（最纯、最稳、production 最安全）；
`混合（mixed）`掺官方 + 其他通道；`逆向（reverse）`从网页版反向工程（最便宜、
最不稳、违反 ToS 风险最高）。信任排序：官转 > 混合 > 聚合 > 逆向。

### 怎么判断中转站偷偷降智（换模型）？

做 canary 测试：留 3–5 道已知难题，先记下官方 API 的基准，再每周对中转站跑同
样的题目，比对推理深度与格式遵循度。对 28 个中转站的研究发现 45.83% 的端点返
回的模型与请求不符——降智常常在你充值"之后"才出现。

### 中转站 vs OpenRouter vs 官方 API，怎么选？

官方 API：最可靠，需国外信用卡。OpenRouter 等海外聚合：官方授权、加价约 5%、
支持卡/加密货币——付得了款的话是"干净选择"。中国/亚洲中转站：最便宜、收支付宝/
微信，但质量浮动、有运营者风险。production 或敏感数据请走官方或自托管网关。

### 中转站和镜像站差在哪？

镜像站是给一般人用的代理版聊天网页（像被转贴的 ChatGPT 页面）。中转站是给开发
者与程序用的 API 接口。本清单只收中转站与网关。

### 哪些国家需要中转站？只有中国吗？

不是。中转站出现在任何**访问封锁 + 支付障碍**并存的地方。中国生态最深；俄罗斯/
白俄/伊朗面临硬封锁（连 VPN 都被识别）+ 受制裁银行卡被拒；亚太含台湾多半能连
但卡在信用卡被拒与账单麻烦。它是全球性回应，不是中国独有。

## 参与贡献

本清单**持续维护**、社区驱动。新增/纠错站点、标记跑路站、补充有据可查的风险案例：

- 阅读 [CONTRIBUTING.md](CONTRIBUTING.md) 与[字段规范](data/schema.md)。
- 编辑 [`data/providers.yaml`](data/providers.yaml)，**不要**直接改 README 表格。
- 用 [provider 模板](.github/ISSUE_TEMPLATE) 开 issue 提交新增。

**不接受**推广链接或营销文案。只收事实、带日期、有来源的条目。

## 许可

[![CC0](https://licensebuttons.net/p/zero/1.0/80x15.png)](LICENSE) —
在法律允许范围内，贡献者已放弃本作品的一切著作权及相关权利（[CC0 1.0](LICENSE)）。

## 免责声明

本仓库是信息性目录，**不构成**对任何服务的推荐。许多中转站处于法律灰色地带，
可能违反上游厂商的服务条款。使用中转站可能将你的 prompt、代码与数据暴露给
不可追责的第三方。请自行评估风险并遵守适用法律与合同。
