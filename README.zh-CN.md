# Awesome AI API 中转站 [![Awesome](https://awesome.re/badge.svg)](https://awesome.re)

> 一份**持续维护**的 AI API 中转站 / 代理（"中转站"）、全球 LLM 网关，
> 以及评估工具的清单 —— 基于证据，讲清楚这个市场为什么存在、风险在哪。

**语言：** [English](README.md) · [繁體中文](README.zh-TW.md) · 简体中文

最后审阅：**2026-05-26** · 维护者 [@howardpen9](https://github.com/howardpen9) ·
欢迎贡献 —— 见 [CONTRIBUTING.md](CONTRIBUTING.md)

---

## 目录

- [什么是 API 中转站](#什么是-api-中转站)
- [为什么会出现（全球视角）](#为什么会出现全球视角)
- [中国 / 亚洲中转站](#中国--亚洲中转站)
- [海外网关与聚合平台](#海外网关与聚合平台)
- [自托管替代方案](#自托管替代方案)
- [对比与监控工具](#对比与监控工具)
- [如何安全地挑选](#如何安全地挑选)
- [Canary 验证 prompt（检测偷偷降智）](#canary-验证-prompt检测偷偷降智)
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
> **最后验证**＝维护者最后一次访问该站的日期；unverified 条目没有此字段。
> 价格变动极快，请以官网为准。数据生成自 [`data/providers.yaml`](data/providers.yaml)。

| 中转站 | 类型 | 支付 | 状态 | 最后验证 | 公司主体 | 备注 |
|---|---|---|---|---|---|---|
| [云雾 API (YUNWU)](https://yunwu.ai) | mixed | 支付宝/微信 | active | 2026-05-26 | 未知 | 主打高速稳定；社区常列为头部站。 |
| [柏拉图 AI (bltcy)](https://api.bltcy.ai) | mixed | 支付宝/微信 | active | 2026-05-26 | 未知 | Azure 通道；主打最低价。 |
| [No.1-API](https://api.rcouyi.com) | aggregator | 支付宝/微信 | active | 2026-05-26 | 未知 | 一站式聚合 + 中转平台。 |
| [UiUiAPI](https://uiuiapi.com) | official-relay | 支付宝/微信 | active | 2026-05-26 | 未知 | 宣称官方渠道 + 官方倍率；约便宜 49%（宣称），300+ 模型。 |
| [DMXAPI](https://dmxapi.cn) | mixed | 支付宝/微信 | unverified | — | 未知 | 社区收录；官网未独立核实。 |
| [MKEAI](https://mkeai.com) | mixed | 支付宝/微信 | unverified | — | 未知 | 社区论坛 + 中转混合；主推 DeepSeek。 |
| [GPTGOD](https://gptgod.online) | reverse | 支付宝 | unverified | — | 未知 | 逆向；便宜，稳定性无保证。 |
| [CloseAI](https://www.closeai-asia.com) | official-relay | 支付宝/微信/对公 | active | 2026-05-26 | 已注册 | 提供对公发票；自称亚洲最大企业级中转。 |

> **收录 ≠ 推荐。** 收录是为了记录市场。打款或传数据前请先走
> [评估清单](docs/evaluation.md)。

## 海外网关与聚合平台

| 服务 | 类型 | 支付 | 备注 |
|---|---|---|---|
| [OpenRouter](https://openrouter.ai) | aggregator | 卡/加密货币 | 官方授权路由，加价约 5%；400+ 模型、60+ 供应商。ARR 据报约 $5M（2025-05）→ 约 $50M（2026 初）。 |
| [LiteLLM](https://litellm.ai) | gateway-oss | — | 开源网关（100+ 供应商）+ 企业版。自托管，自带 Key。 |
| [Helicone](https://helicone.ai) | observability | — | LLM 可观测性网关；日志/成本分析。 |
| [AIMLAPI](https://aimlapi.com) | aggregator | 卡/加密货币 | 400+ 模型，$20 起预付；支持加密货币暗示绕支付障碍。 |

## 自托管替代方案

这些不是中转站，而是**自托管网关**——当你不希望第三方夹在请求路径中时的可信选项。
你自带上游官方 key（或自负风险使用中转站 key）、跑在自己的机器上、数据留在自己手中。
大部分中国中转站本身就是用这些开源项目搭起来的。

| 项目 | 类型 | 备注 |
|---|---|---|
| [One-API](https://github.com/songquanpeng/one-api) | gateway-oss | 流行的 Go 多厂商网关；多数中转站的底层 OSS 模板。 |
| [new-api](https://github.com/Calcium-Ion/new-api) | gateway-oss | One-API 的 fork，多了几种通道类型；同样自托管、自带 key。 |
| [LiteLLM](https://litellm.ai) | gateway-oss | 上面列过，Python 为主、100+ 供应商、企业常用。 |

**什么时候该自托管而非用中转站**：合规/敏感数据、production 工作负载、你已经能用国外卡付款、
或需要可审计的日志。代价是失去支付宝/微信的便利，并承担运维成本。

## 对比与监控工具

| 工具 | 备注 |
|---|---|
| [中转站竞技场 (AI API PK)](https://www.aiapipk.com) | 约 40 家站点的 OpenAI / 逆向 / Claude / DeepSeek 报价墙。 |
| [awesome-ai-proxy (mn-api)](https://github.com/mn-api/awesome-ai-proxy) | 最早的清单（约 31 家）。**2026 年起已停更** —— 本仓库延续这一工作。 |

## 如何安全地挑选

完整框架见 **[docs/evaluation.md](docs/evaluation.md)**。速览：

1. **先看通道类型** —— `official-relay` > `mixed` > `aggregator` > `reverse`。
2. **做 canary 测试** —— 用已知难题，官方 vs 中转，每周比对，识别偷偷降智。可直接复制的 prompt 集：**[docs/canary-prompts.md](docs/canary-prompts.md)**。
3. **小额充值** —— 中转站基本都是预付，绝不大额预存。
4. **按场景匹配** —— 敏感/合规数据走官方 API 或自托管 `gateway-oss`，绝不用 `reverse`。

## Canary 验证 prompt（检测偷偷降智）

对抗"中转站偷偷换成便宜模型"最有效的方法，就是一组固定、可复现的 **canary
prompt**，每周对官方 API 与中转站都跑一次，比对结果。

完整 prompt 集、每个模型族（GPT-4 级、Claude Opus 级、Gemini 2.5 Pro 级）的
预期基准行为与 pass/fail 评分准则，全部在 **[docs/canary-prompts.md](docs/canary-prompts.md)**。
拿来直接用、或 fork 一份自己的版本都可以。

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

### Claude API（Sonnet / Opus）哪家中转站最推荐？

**没有单一一家可以安全推荐**——Anthropic 条款比 OpenAI 严、Claude key 被轮换和
封禁得更积极，今天看起来稳的站可能一夜之间崩。实务建议：

- production 跑 Claude：用官方 Anthropic API，或注册有公司主体的全球聚合（如
  [OpenRouter](https://openrouter.ai)，官方授权、加价约 5%、支持 Claude）。
- 实验用途：优先挑上方表格中 `official-relay` 类型的站，**充值前**先跑
  **[docs/canary-prompts.md](docs/canary-prompts.md)** 确认真的有回传真实模型。
- 任何宣称"Claude Opus 一折"的站，预设当成 `reverse` 通道——这个价格只可能来自
  网页版逆向工程或偷偷降智。

### 怎么判断一家中转站快跑路了？

实证来看，跑路有共同模式。红旗按严重度排序：

1. **没有注册公司／没有 ICP 备案**——17 家头部站中 15 家无备案。
2. **大力推预付赠送**（"充 100 送 50"），先吸大量余额再消失。
3. **价格低于物理成本**（官方 1/10 ～ 1/50）——钱一定从某处节省下来。
4. **Canary 开始退步**——以前能通过的题目开始不行（约 70% 跑路案例的前兆）。
5. **客服变慢／消失、账单页面坏掉、ICP 过期、社群账号静默。**

缓解：只小额充值、绝不大额预存；订阅中转站追踪频道（V2EX、[risks.md](docs/risks.md)）。

### 我该用中转站还是自托管 One-API／LiteLLM？

只要符合以下任一条件，就用**自托管网关**：受监管或客户数据、production 工作负载、
你已经能用国外卡付款、需要可审计日志。Key 放在自己机房，没有不可追责的第三方
经手。

中转站只适合：低风险实验、学习、副业项目、或你真的拿不到国外卡。传过去的任何
东西都当成公开数据看待。详见[自托管替代方案](#自托管替代方案)。

### 台湾 / 香港 / 东南亚用中转站划算吗？

**边际效益不高。** 网络访问本来就 OK，所以真正的好处只剩 (a) 支付宝/微信付款
免国外卡、(b) 一个 key 打通多厂商。代价是 prompt 经过一个中国法域、没有合约
约束的第三方——这个交换比通常不划算。

对多数台/港/东南亚开发者，更好的组合是：
1. 拿得到卡的厂商就用官方 API，
2. 想要多厂商便利就用 [OpenRouter](https://openrouter.ai)，
3. 真的需要统一 key 就自托管一份 [One-API](https://github.com/songquanpeng/one-api) 或
   [LiteLLM](https://litellm.ai)。

中转站主要适合：完全拿不到国外卡的情况。

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
