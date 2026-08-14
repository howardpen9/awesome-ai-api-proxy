# Awesome AI API 中轉站 [![Awesome](https://awesome.re/badge.svg)](https://awesome.re)

> **一個給 AI agent 的價格端點。** 不用再手動打開 10 家中轉站的價格頁 —— 把 agent 指過來這裡。

### 🤖 給 AI agent —— 三種取用方式

```bash
# 1) 純 JSON（全部中轉站的價格、附完整出處）
curl https://raw.githubusercontent.com/howardpen9/awesome-ai-api-proxy/main/data/prices.latest.json

# 2) MCP server（Claude Desktop / Cursor / Cline）—— 模型自己會叫 tool
uvx awesome-ai-api-proxy-mcp

# 3) 給人類看的互動 dashboard
open https://howardpen9.github.io/awesome-ai-api-proxy/
```

**內容：**7 個中轉站 fetcher 每週自動爬、~3000 條標準化價格、6 個 canonical 模型在 cost-tier ladder 上、每筆都帶完整出處（`source_url` + `captured_at` + `method`）讓 agent 可以引用得有底氣。MCP / LangChain / OpenAI function-calling / 純 HTTP 範例見 [docs/agent-integration.md](docs/agent-integration.md)。

---

**語言：** [English](README.md) · 繁體中文 · [简体中文](README.zh-CN.md)

最後審閱：**2026-07-12** · 維護者 [@howardpen9](https://github.com/howardpen9) ·
歡迎貢獻 —— 見 [CONTRIBUTING.md](CONTRIBUTING.md)

---

## 目錄

- [給 AI agent 與程式化使用](#給-ai-agent-與程式化使用) ← 從這裡開始
- [價格快照（每週更新）](#價格快照每週更新)
- [什麼是 API 中轉站](#什麼是-api-中轉站)
- [為什麼會出現（全球視角）](#為什麼會出現全球視角)
- [中國 / 亞洲中轉站](#中國--亞洲中轉站)
- [海外閘道與聚合平台](#海外閘道與聚合平台)
- [自架替代方案](#自架替代方案)
- [對比與監控工具](#對比與監控工具)
- [想被收錄嗎？](#想被收錄嗎)
- [如何安全地挑選](#如何安全地挑選)
- [Canary 驗證 prompt（偵測偷偷降智）](#canary-驗證-prompt偵測偷偷降智)
- [風險（務必閱讀）](#風險務必閱讀)
- [市場背景](#市場背景)
- [常見問題 FAQ](#常見問題-faq)
- [參與貢獻](#參與貢獻)

---

## 什麼是 API 中轉站

> **API 中轉站（AI API Relay）是一個轉發端點，夾在你的程式碼和官方 LLM API
> 之間。** 你把 `base_url` 改成中轉站、用它給的 key，就能呼叫 OpenAI / Claude /
> Gemini 等數十種模型——一個 key、人民幣付款（支付寶/微信）、低延遲，通常比官方
> 便宜 30–90%。

**API 中轉站**（也叫「AI API 代理 / Relay」）是一個中間轉發端點。你不直接打
OpenAI、Anthropic、Google 等官方 API，而是把 `base_url` 改成中轉站位址、用它
給的 Key。中轉站幫你轉發到官方後端再把結果回傳 —— 通常**完全相容 OpenAI 格式**，
程式碼幾乎不用改。

一個 Key 打通幾十到上百種跨廠商模型。

它和**鏡像站**不同：鏡像站是給一般人用的代理版聊天網頁；中轉站是給
**開發者與程式**用的介面。

## 為什麼會出現（全球視角）

中轉站不是中國獨有，而是**存取封鎖 + 支付障礙**這兩個痛點共同的產物：

| 地區 | 存取障礙 | 支付障礙 |
|---|---|---|
| 中國 | 跨境延遲高、部分 API 不可用 | 需國外信用卡；中轉站收支付寶/微信 |
| 俄羅斯 / 白俄 / 伊朗 | OpenAI 硬封鎖（連 VPN 都被偵測） | 受制裁銀行卡（如伊朗 Shetab）被拒 |
| 亞太含台灣 | 通常可連 | 信用卡被拒、額度限制、帳單麻煩 |
| 受制裁 / 受限市場 | 註冊被拒 | 沒有可用的支付通道 |

同樣的需求長出不同生態：俄羅斯靠 IP 代理 + 國產替代（如 GigaChat），中國則演化
出完整的**中轉站零售業**。全球「乾淨版」是官方授權聚合平台（見下方 OpenRouter）
—— 證明「統一呼叫多廠商模型」是真實成長的市場，而非小眾繞路。

## 中國 / 亞洲中轉站

> **怎麼讀這張表：** 🟢 = `active` 且維護者親自 canary 過 · 🟡 = 社群登錄或 `unverified` · 🔴 = `inactive`／跑路。
>
> **信任** = 狀態 + 最後驗證日期 +（若公開可見公司主體會多 `· 已註冊`）+（已知安全顧慮會多 `· ⚠ <旗標>`）。常見旗標：`自薦`（營運者自薦）、`無主體`（無公開公司／ICP）、`逆向`（逆向通道）、`價過低`（價格遠低於 OR，多半降智）、`跑路`（已捲款）。完整 enum 見 [`data/schema.md`](data/schema.md#risk_flags-enum-schema-v5)。
>
> 價格變動極快，請以官網為準。完整欄位（payment、models、supports_tools 等）在 [`data/providers.yaml`](data/providers.yaml)；下面的表格由 [`scripts/build_provider_tables.py`](scripts/build_provider_tables.py) 自動生成。

<!-- providers:china_relays:start -->
| 中轉站 | 類型 | 支付 | 信任 | 備註 |
|---|---|---|---|---|
| 🟢 [云雾 API (YUNWU)](https://yunwu.ai) | mixed | 支付寶/微信 | active · 2026-05-26 | 主打高速穩定；社群常列為頭部站。 |
| 🟢 [柏拉图 AI (bltcy)](https://api.bltcy.ai) | mixed | 支付寶/微信 | active · 2026-06-07 | Azure 通道；主打最低價。new-api fork，1000+ 模型橫跨 25+ 分組；`/api/pricing` 公開 default 分組倍率。 |
| 🟢 [No.1-API](https://api.rcouyi.com) | aggregator | 支付寶/微信 | active · 2026-05-26 | 一站式聚合 + 中轉平台。 |
| 🟢 [UiUiAPI](https://uiuiapi.com) | official-relay | 支付寶/微信 | active · 2026-06-07 | 宣稱官方渠道 + 官方倍率；約便宜 49%（宣稱），311 模型。new-api `/api/pricing` 公開於 api1 子網域。 |
| 🟡 [DMXAPI](https://dmxapi.cn) | mixed | 支付寶/微信 | unverified · ⚠ 無主體 | 社群收錄；官網未獨立核實。 |
| 🟡 [MKEAI](https://mkeai.com) | mixed | 支付寶/微信 | unverified · ⚠ 無主體 | 社群論壇 + 中轉混合；主推 DeepSeek。 |
| 🟡 [GPTGOD](https://gptgod.online) | reverse | 支付寶 | unverified · ⚠ 逆向, 無主體 | 逆向；便宜，穩定性無保證。 |
| 🟢 [CloseAI](https://www.closeai-asia.com) | official-relay | 支付寶/微信/對公 | active · 2026-05-26 · 已註冊 | 提供對公發票；自稱亞洲最大企業級中轉。 |
<!-- providers:china_relays:end -->

> **收錄 ≠ 推薦。** 收錄是為了記錄市場。打款或傳資料前請先走
> [評估清單](docs/evaluation.md)。

## 海外閘道與聚合平台

<!-- providers:global_gateways:start -->
| 服務 | 類型 | 支付 | 備註 |
|---|---|---|---|
| 🟢 [OpenRouter](https://openrouter.ai) | aggregator | 卡/加密貨幣 | 官方授權路由，加價約 5%；400+ 模型、60+ 供應商。ARR 據報約 $5M（2025-05）→ 約 $50M（2026 初）。公開 `/api/v1/models` JSON。 |
| 🟢 [Atlas Cloud](https://www.atlascloud.ai) | aggregator | 卡 | 多模態聚合平台；影像/影片模型多（Grok Imagine、Kling、ByteDance、Vidu）。公開 OpenAI 相容 `/v1/models` 含 cache-read 計價。 |
| 🟢 [Relaydance](https://relaydance.com) | mixed | 支付寶/微信/卡 | 基於 new-api 的中文介面海外站，主打 xAI Grok + 字節跳動 Doubao。`/api/pricing` 公開倍率計價（model_ratio × $2/1M tokens）。 |
| 🟢 [LiteLLM](https://litellm.ai) | gateway-oss | — | 開源閘道（100+ 供應商）+ 企業版。自架，自帶 Key。 |
| 🟢 [Helicone](https://helicone.ai) | observability | — | LLM 可觀測性閘道；日誌/成本分析。 |
| 🟢 [AIMLAPI](https://aimlapi.com) | aggregator | 卡/加密貨幣 | 400+ 模型，$20 起預付；支援加密貨幣暗示繞支付障礙。 |
| 🟡 [RouteScope](https://www.routescope.ai) | aggregator | 卡/加密貨幣 | 統一閘道，將 100+ 模型轉成 OpenAI／Claude／Gemini 相容 API；按量預付額度。 |
| 🟡 [UnoRouter](https://unorouter.ai) | aggregator | 卡 | 建於 new-api 閘道之上。單一金鑰跨多上游，依延遲路由並具故障轉移；自動辨識 OpenAI／Anthropic／Gemini 格式。按量計費並提供免費模型層；亦支援角色扮演用戶端（SillyTavern、Janitor.AI、RisuAI、Chub）。 |
<!-- providers:global_gateways:end -->

## 自架替代方案

這些不是中轉站，而是**自架閘道**——當你不希望第三方夾在請求路徑中時的可信選項。
你自帶上游官方 key（或自負風險使用中轉站 key）、跑在自己的機器上、資料留在自己手中。
大部分中國中轉站本身就是用這些開源專案搭起來的。

<!-- providers:self_hosted_alternatives:start -->
| 專案 | 類型 | 備註 |
|---|---|---|
| 🟢 [One-API](https://github.com/songquanpeng/one-api) | gateway-oss | 流行的 Go 多廠商閘道；多數中轉站的底層 OSS 模板。 |
| 🟢 [new-api](https://github.com/Calcium-Ion/new-api) | gateway-oss | One-API 的 fork，多了幾種通道類型；同樣自架、自帶 key。 |
| 🟡 [A3M Router](https://github.com/Das-rebel/a3m-router) | gateway-oss | MIT TypeScript OpenAI-compatible multi-provider router (parallel ensemble); self-hosted — you supply keys. npm: adaptive-memory-multi-model-router. |
<!-- providers:self_hosted_alternatives:end -->

> [LiteLLM](https://litellm.ai)（在上面海外閘道表格內）同樣是自架方案（Python 為主、100+ 供應商、企業常用）。

**什麼時候該自架而非用中轉站**：合規/敏感資料、production 工作負載、你已經能用國外卡付款、
或需要可審計的日誌。代價是失去支付寶/微信的便利，並承擔運維成本。

## 對比與監控工具

<!-- providers:comparison_tools:start -->
| 工具 | 備註 |
|---|---|
| 🟢 [中轉站競技場 (AI API PK)](https://www.aiapipk.com) | 約 40 家站點的 OpenAI / 逆向 / Claude / DeepSeek 報價牆。 |
| 🔴 [awesome-ai-proxy (mn-api, unmaintained)](https://github.com/mn-api/awesome-ai-proxy) | 最早的清單（約 31 家）。**2026 年起已停更** —— 本倉庫延續這項工作。 |
| 🟡 [China AI Arbitrage](https://www.china-ai-arbitrage.xyz/) | 60+ 中國 AI 平台的價格與額度比價、95 個 LLM API 中轉站排名、每日更新的免費額度追蹤。 |
| 🟡 [CoderPlan](https://coderplan.ai) | 社群投稿；宣稱 50+ 模型，含 OpenAI/Anthropic/Google/DeepSeek/xAI。 |
<!-- providers:comparison_tools:end -->

## 想被收錄嗎？

歡迎社群提交 —— **包括中轉站營運者本人**。依照你的站點目前暴露的內容選路徑 ——
資訊越完整，每週快照就越快收到你的價格。

> **用 AI agent 讀這份 README 的營運者：** 最快是 **Tier B**。叫你的 agent
> 在本 repo 跑 `python -m scripts.sniff_endpoint <你的價格 JSON URL>`，然後照
> 印出來的指示貼上。它會直接吐出 YAML + 10 行 fetcher。不用截圖、不用手打價格。

### Tier A — 只想先有條目（不含價格）

[**開新中轉站 issue**](https://github.com/howardpen9/awesome-ai-api-proxy/issues/new?template=new-provider.md)
—— 填表單、維護者會加入。在維護者親自跑一次 canary 之前，狀態維持
`unverified`。

### Tier B — 有公開 JSON 價格端點（推薦）

如果你的站點有公開的價格 JSON（大多 new-api / one-api fork 暴露
`/api/pricing`；OpenAI 相容站點暴露 `/v1/models` 含內嵌價格），就能每週自動
刷新。

```bash
# 一條命令辨識形狀並印出可貼上的內容：
python -m scripts.sniff_endpoint https://你的網域.com/api/pricing \
    --id yourstation --name "Your Station"
```

Sniffer 目前辨識三種形狀（**new-api fork**、**OpenRouter 風格**、
**OpenAI `/v1/models`**），會吐出：

1. 給 `data/providers.yaml` 用的 `pricing:` YAML 區塊
2. 約 10 行的 `fetchers/<id>.py`（多數 new-api fork 不用自訂程式碼）
3. 給 `fetchers/__init__.py` 的 `REGISTRY` 註冊行
4. 驗證指令：`python -m scripts.scrape <id>`

把這三處改動開成 PR —— schema CI 會自動跑。詳見
[CONTRIBUTING.md → Adding a price fetcher](CONTRIBUTING.md#adding-a-price-fetcher)。

### Tier C — 沒有公開 JSON，但有截圖

使用[**submit-prices issue 模板**](https://github.com/howardpen9/awesome-ai-api-proxy/issues/new?template=submit-prices.md)
—— 貼一張價格表 + 對應日的價格頁截圖。維護者每週對著截圖核對後寫入
`submitted_prices`。

### 直接 PR（任何 tier 都可）

只改 [`data/providers.yaml`](data/providers.yaml)（README 表格自動重新生成）。
schema 見 [CONTRIBUTING.md](CONTRIBUTING.md)；
[PR template](.github/pull_request_template.md) 有逐項 checklist。

---

**預設 `status: unverified`**，直到維護者親自跑一次 canary。這不是拒絕 ——
只是表示「社群登錄、未獨立確認」。通常 2 週內驗證完，狀態改成 `active`、
寫入 `last_verified`。

我們不收 referral 連結、不收行銷文案。但**接受營運者自薦**——
`notes` 寫一句事實、不要最高級形容詞就好。

> **每個 PR 自動跑 schema CI**（[pr-validate workflow](.github/workflows/pr-validate.yml)）—— 欄位拼錯或 `type` 不合法，bot 會先告訴你、不用等維護者抓。

## 價格快照（每週更新）

> 為什麼按 tier 分組：頂尖 10 個前沿模型的價格相差 **10 倍**
> （Chamath 在 2025–2026 年的觀察）。新的競爭優勢是 *路由* —— 把日常 token
> 交給最便宜的可用模型、把最難的推理交給最貴的。要會路由，前提是看得到價差；
> 這個段落就是價差層。

> 由 [`scripts/build_prices.py`](scripts/build_prices.py) 從
> [`data/snapshots/`](data/snapshots/) 每週生成。
> 機器可讀資料：[`data/prices.latest.json`](data/prices.latest.json)。

<!-- prices:start -->
_Snapshot date: **2026-07-17**. 3023 price records across 4 providers. **Reference column** is OpenRouter (officially-authorized, ~5% markup). Rows sorted cheapest-by-OpenRouter first. ⚠ = relay quotes <50% of OpenRouter — verify with [canary prompts](docs/canary-prompts.md) before trusting._

#### Six indicator models, six providers, one snapshot

**Absolute prices — tier ladder (input)** · ▼ marks the cheapest provider per model

![Tier-ladder input pricing](assets/charts/tier-ladder-input.svg)

**Price spread per model (input)** · how much variance exists between providers

![Spread range input](assets/charts/spread-range-input.svg)

**Savings vs OpenRouter (input)** · how much cheaper (or pricier) each relay is

![Savings vs OpenRouter input](assets/charts/savings-vs-ref-input.svg)

_Output-token equivalents and the full-matrix heatmap: [`assets/charts/`](assets/charts/) ([tier-ladder-output](assets/charts/tier-ladder-output.svg), [spread-range-output](assets/charts/spread-range-output.svg), [savings-vs-ref-output](assets/charts/savings-vs-ref-output.svg), [spread-heatmap-input](assets/charts/spread-heatmap-input.svg)). Interactive dashboard: <https://howardpen9.github.io/awesome-ai-api-proxy/>._

### Tier 1 — cheapest viable (routine, batch summaries) — USD per 1M input tokens

| Model | OpenRouter (ref) | Atlas Cloud | UiUiAPI | bltcy |
|---|---|---|---|---|
| `deepseek-v3` | $0.200 | — | $2.000 | $2.000 |
| `deepseek-r1` | $0.700 | — | $4.000 | $4.000 |

### Tier 2 — daily driver (agent, coding) — USD per 1M input tokens

| Model | OpenRouter (ref) | Atlas Cloud | UiUiAPI | bltcy |
|---|---|---|---|---|
| `gemini-3-flash` | $1.500 | $1.500 | $1.500 | — |
| `gpt-5.4` | $2.500 | $2.500 | — | $2.500 |
| `claude-sonnet-4.6` | $3.000 | $3.000 | $3.000 | $3.000 |

### Tier 3 — top frontier (hardest problems) — USD per 1M input tokens

| Model | OpenRouter (ref) | Atlas Cloud | UiUiAPI | bltcy |
|---|---|---|---|---|
| `grok-4.3` | $1.250 | $1.250 | — | — |
| `claude-opus-4.8` | $5.000 | $5.000 | — | — |
| `gpt-5.5-pro` | $30.00 | — | — | — |

### Tier 4 — multimodal (different units, can't compare to text)

| Model | Unit | OpenRouter (ref) | Atlas Cloud | UiUiAPI | bltcy |
|---|---|---|---|---|---|
| `grok-imagine-video-1.5` | USD per second | — | — | — | $1.000 |

_Full per-model breakdown (including non-canonical models): [`docs/prices.md`](docs/prices.md). Raw snapshots: [`data/snapshots/`](data/snapshots/). Machine-readable: [`data/prices.latest.json`](data/prices.latest.json)._

<!-- prices:end -->

### 品質參考（搭配這份價格資料用）

這個 repo 追蹤**價格**且每筆都有完整出處。**品質／智力**我們刻意連結出去到既有 benchmark，而不是把分數抄進來（分數衰退快、需要持續維護）。把我們的價格資料搭配以下其一使用：

- **[Terminal Bench](https://www.tbench.ai/)** —— 真實 terminal 驅動 agent 任務的完成率。最貼近 coding／agent 場景。
- **[Kilo Code 排行榜](https://kilo.ai/leaderboard)** —— 真實開發者 token 用量排名 + cost-per-attempt × completion-% 散佈圖。已經幫你畫好 Pareto 前緣。
- **[lmarena ELO](https://arena.ai/leaderboard)** —— 來自盲測雙模型偏好投票的 ELO 分數。一般 chat 場景最常被引用。

路由經驗法則：**在你品質預算內的模型，挑這份資料裡最便宜的 provider**。完整 benchmark 清單也在 [`data/canonical-models.yaml`](data/canonical-models.yaml#benchmark_references)，agent 可透過 MCP server 取用。

## 給 AI agent 與程式化使用

這個 repo 的資料層**刻意設計給 LLM agent 引用**——回答中轉站價格問題時，
agent 應該直接讀以下穩定 URL，而不是解析 markdown：

| 內容 | URL |
|---|---|
| 最新標準化價格（JSON） | `https://raw.githubusercontent.com/howardpen9/awesome-ai-api-proxy/main/data/prices.latest.json` |
| 中轉站清單（YAML） | `https://raw.githubusercontent.com/howardpen9/awesome-ai-api-proxy/main/data/providers.yaml` |
| 標準化模型登錄（YAML） | `https://raw.githubusercontent.com/howardpen9/awesome-ai-api-proxy/main/data/canonical-models.yaml` |
| 每週快照（瀏覽） | <https://github.com/howardpen9/awesome-ai-api-proxy/tree/main/data/snapshots> |
| LLM 站點地圖 | `https://raw.githubusercontent.com/howardpen9/awesome-ai-api-proxy/main/llms.txt` |

`prices.latest.json` 每筆記錄帶有 `provider_id`、`raw_model_name`、
`canonical_model`、`unit`、`price_usd`、`source_url`、`captured_at`、`method`
—— 這是**引用信封**。Agent 引用價格時請帶上 `captured_at` 與 `source_url`，
使用者才能驗證。

```python
import httpx
data = httpx.get(
    "https://raw.githubusercontent.com/howardpen9/awesome-ai-api-proxy/main/data/prices.latest.json"
).json()
for rec in data["records"]:
    if rec.get("canonical_model") == "grok-4.3" and rec["unit"] == "per_1m_input_tokens":
        print(f"{rec['provider_name']}: ${rec['price_usd']}/1M ({rec['captured_at']})")
```

## 如何安全地挑選

完整框架見 **[docs/evaluation.md](docs/evaluation.md)**。速覽：

1. **先看通道類型** —— `official-relay` > `mixed` > `aggregator` > `reverse`。
2. **做 canary 測試** —— 用已知難題，官方 vs 中轉，每週比對，識別偷偷降智。可直接複製的 prompt 集：**[docs/canary-prompts.md](docs/canary-prompts.md)**。
3. **小額充值** —— 中轉站基本都是預付，絕不大額預存。
4. **按場景匹配** —— 敏感/合規資料走官方 API 或自架 `gateway-oss`，絕不用 `reverse`。

## Canary 驗證 prompt（偵測偷偷降智）

對抗「中轉站偷偷換成便宜模型」最有效的方法，就是一組固定、可重現的 **canary
prompt**，每週對官方 API 與中轉站都跑一次，比對結果。

完整 prompt 集、每個模型族（GPT-4 級、Claude Opus 級、Gemini 2.5 Pro 級）的
預期基準行為與 pass/fail 評分準則，全部在 **[docs/canary-prompts.md](docs/canary-prompts.md)**。
拿來直接用、或 fork 一份自己版本都可以。

## 風險（務必閱讀）

市場基本無監管。來自公開研究：

- 一項對 **28 個中轉站**的測試發現 **45.83% 的 API 端點回傳的模型與請求不符**
  （醫療任務效能差距達 47%）。
- 對 **428 個站點**的稽核發現 **9 個注入惡意程式碼**、**1 個直接盜取資金**。
- 調研 17 家頭部站，**15 家無註冊公司**。

完整說明與來源見 **[docs/risks.md](docs/risks.md)**。

## 市場背景

- 最早的社群清單（[mn-api/awesome-ai-proxy](https://github.com/mn-api/awesome-ai-proxy)）
  收錄約 31 家後停更；aiapipk.com 等聚合約 40 家 —— 這只是冰山一角。
- 「乾淨版」全球對應物 OpenRouter，據報不到一年 ARR 成長約 10 倍（約 $5M → 約
  $50M），月處理兆級 token —— 強力證明「統一多廠商存取」是可持續市場。
- 結論：中轉站是**封鎖 + 支付障礙的全球性回應**，中國生態最深，因為兩個痛點
  在那裡最集中。

## 給台灣使用者的提醒

台灣網路環境比大陸好，**官方 API 大多可直接用**。中轉站對台灣使用者的價值主要
在：某些模型更便宜、想一個 Key 管理多廠商、想用更簡單的儲值方式。但代價是
prompt/資料經過第三方 —— 商用或敏感場景請優先官方 API。

## 常見問題 FAQ

### API 中轉站是什麼？

API 中轉站是夾在你的程式碼和官方 LLM API（OpenAI、Anthropic、Google）之間的
轉發端點。你把 `base_url` 改成中轉站、用它給的 key，它幫你轉發到官方後端再回
傳結果，通常完全相容 OpenAI 格式。一個 key 就能用幾十到上百種跨廠商模型。

### API 中轉站安全嗎？會被盜 key 或偷 prompt 嗎？

把每個中轉站都當成不可信的中間人。它能看到你所有的 prompt、回應和傳出去的
資料——惡意營運者可以記錄、竄改或外洩。對 428 個站點的稽核發現 9 個注入惡意
程式碼、1 個直接盜資金。絕不要透過中轉站傳密鑰或受規管資料；敏感場景請用官方
API 或自架閘道。

### API 中轉站為什麼比官方便宜這麼多？

三個原因：上游批發價、混合通道（如 Azure 額度）、以及最便宜那一檔的「逆向」
（從廠商網頁版反向工程）。價格只有官方 1/10 到 1/50 的，通常代表逆向通道或偷
偷降智，不是真的撿到便宜。

### 官轉、混合、逆向差在哪？哪個能用在 production？

`官轉（official-relay）`轉發真正的官方 key（最純、最穩、production 最安全）；
`混合（mixed）`摻官方 + 其他通道；`逆向（reverse）`從網頁版反向工程（最便宜、
最不穩、違反 ToS 風險最高）。信任排序：官轉 > 混合 > 聚合 > 逆向。

### 怎麼判斷中轉站偷偷降智（換模型）？

做 canary 測試：留 3–5 題已知難題，先記下官方 API 的基準，再每週對中轉站跑同
樣的題目，比對推理深度與格式遵循度。對 28 個中轉站的研究發現 45.83% 的端點回
傳的模型與請求不符——降智常常在你充值「之後」才出現。

### 中轉站 vs OpenRouter vs 官方 API，怎麼選？

官方 API：最可靠，需國外信用卡。OpenRouter 等海外聚合：官方授權、加價約 5%、
支援卡/加密貨幣——付得了款的話是「乾淨選擇」。中國/亞洲中轉站：最便宜、收支付
寶/微信，但品質浮動、有營運者風險。production 或敏感資料請走官方或自架閘道。

### 中轉站和鏡像站差在哪？

鏡像站是給一般人用的代理版聊天網頁（像被轉貼的 ChatGPT 頁面）。中轉站是給開發
者與程式用的 API 介面。本清單只收中轉站與閘道。

### 哪些國家需要中轉站？只有中國嗎？

不是。中轉站出現在任何**存取封鎖 + 支付障礙**並存的地方。中國生態最深；俄羅斯/
白俄/伊朗面臨硬封鎖（連 VPN 都被偵測）+ 受制裁銀行卡被拒；亞太含台灣多半能連
但卡在信用卡被拒與帳單麻煩。它是全球性回應，不是中國獨有。

### Claude API（Sonnet / Opus）哪家中轉站最推薦？

**沒有單一一家可以安全推薦**——Anthropic 條款比 OpenAI 嚴、Claude key 被輪換和
封鎖得更積極，今天看起來穩的站可能一夜之間崩。實務建議：

- production 跑 Claude：用官方 Anthropic API，或註冊有公司主體的全球聚合（如
  [OpenRouter](https://openrouter.ai)，官方授權、加價約 5%、支援 Claude）。
- 實驗用途：優先挑上方表格中 `official-relay` 類型的站，**充值前**先跑
  **[docs/canary-prompts.md](docs/canary-prompts.md)** 確認真的有回傳真實模型。
- 任何宣稱「Claude Opus 一折」的站，預設當成 `reverse` 通道——這個價格只可能來自
  網頁版逆向工程或偷偷降智。

### 怎麼判斷一家中轉站快跑路了？

實證來看，跑路有共同模式。紅旗按嚴重度排序：

1. **沒有註冊公司／沒有 ICP 備案**——17 家頭部站中 15 家無備案。
2. **大力推預付贈送**（「儲 100 送 50」），先吸大量餘額再消失。
3. **價格低於物理成本**（官方 1/10 ～ 1/50）——錢一定從某處節省下來。
4. **Canary 開始退步**——以前能通過的題目開始不行（約 70% 跑路案例的前兆）。
5. **客服變慢／消失、帳單頁面壞掉、ICP 過期、社群帳號靜默。**

緩解：只小額儲值、絕不大額預存；訂閱中轉站追蹤頻道（V2EX、[risks.md](docs/risks.md)）。

### 我該用中轉站還是自架 One-API／LiteLLM？

只要符合以下任一條件，就用**自架閘道**：受規管或客戶資料、production 工作負載、
你已經能用國外卡付款、需要可審計日誌。Key 放在自己機房，沒有不可追責的第三方
經手。

中轉站只適合：低風險實驗、學習、副業專案、或你真的拿不到國外卡。傳過去的任何
東西都當成公開資料看待。詳見[自架替代方案](#自架替代方案)。

### 台灣 / 香港 / 東南亞用中轉站划算嗎？

**邊際效益不高。** 網路存取本來就 OK，所以真正的好處只剩 (a) 支付寶/微信付款
免國外卡、(b) 一個 key 打通多廠商。代價是 prompt 經過一個中國法域、沒有合約
約束的第三方——這個交換比通常不划算。

對多數台/港/東南亞開發者，更好的組合是：
1. 拿得到卡的廠商就用官方 API，
2. 想要多廠商便利就用 [OpenRouter](https://openrouter.ai)，
3. 真的需要統一 key 就自架一份 [One-API](https://github.com/songquanpeng/one-api) 或
   [LiteLLM](https://litellm.ai)。

中轉站主要適合：完全拿不到國外卡的情況。

## 參與貢獻

本清單**持續維護**、社群驅動。新增/糾錯站點、標記跑路站、補充有據可查的風險案例：

- 閱讀 [CONTRIBUTING.md](CONTRIBUTING.md) 與[欄位規範](data/schema.md)。
- 編輯 [`data/providers.yaml`](data/providers.yaml)，**不要**直接改 README 表格。
- 用 [provider 範本](.github/ISSUE_TEMPLATE) 開 issue 提交新增。

**不接受**推廣連結或行銷文案。只收事實、帶日期、有來源的條目。

## 授權

[![CC0](https://licensebuttons.net/p/zero/1.0/80x15.png)](LICENSE) —
在法律允許範圍內，貢獻者已放棄本作品的一切著作權及相關權利（[CC0 1.0](LICENSE)）。

## 免責聲明

本倉庫是資訊性目錄，**不構成**對任何服務的推薦。許多中轉站處於法律灰色地帶，
可能違反上游廠商的服務條款。使用中轉站可能將你的 prompt、程式碼與資料暴露給
不可追責的第三方。請自行評估風險並遵守適用法律與合約。
