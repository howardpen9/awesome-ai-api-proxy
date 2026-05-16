# Awesome AI API 中轉站 [![Awesome](https://awesome.re/badge.svg)](https://awesome.re)

> 一份**持續維護**的 AI API 中轉站 / 代理（「中轉站」）、全球 LLM 閘道，
> 以及評估工具的清單 —— 用證據說清楚這個市場為什麼存在、風險在哪。

**語言：** [English](README.md) · 繁體中文 · [简体中文](README.zh-CN.md)

最後審閱：**2026-05-16** · 維護者 [@howardpen9](https://github.com/howardpen9) ·
歡迎貢獻 —— 見 [CONTRIBUTING.md](CONTRIBUTING.md)

---

## 目錄

- [什麼是 API 中轉站](#什麼是-api-中轉站)
- [為什麼會出現（全球視角）](#為什麼會出現全球視角)
- [中國 / 亞洲中轉站](#中國--亞洲中轉站)
- [海外閘道與聚合平台](#海外閘道與聚合平台)
- [對比與監控工具](#對比與監控工具)
- [如何安全地挑選](#如何安全地挑選)
- [風險（務必閱讀）](#風險務必閱讀)
- [市場背景](#市場背景)
- [參與貢獻](#參與貢獻)

---

## 什麼是 API 中轉站

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

> 狀態：`active` = 可獨立存取；`unverified` = 社群來源，未獨立確認。
> 價格變動極快，請以官網為準。資料生成自 [`data/providers.yaml`](data/providers.yaml)。

| 中轉站 | 類型 | 支付 | 狀態 | 備註 |
|---|---|---|---|---|
| [云雾 API (YUNWU)](https://yunwu.ai) | mixed | 支付寶/微信 | active | 主打高速穩定；社群常列為頭部站。 |
| [柏拉图 AI (bltcy)](https://api.bltcy.ai) | mixed | 支付寶/微信 | active | Azure 通道；主打最低價。 |
| [No.1-API](https://api.rcouyi.com) | aggregator | 支付寶/微信 | active | 一站式聚合 + 中轉平台。 |
| [UiUiAPI](https://uiuiapi.com) | official-relay | 支付寶/微信 | active | 宣稱官方渠道 + 官方倍率；約便宜 49%（宣稱），300+ 模型。 |
| [DMXAPI](https://dmxapi.cn) | mixed | 支付寶/微信 | unverified | 社群收錄；官網未獨立核實。 |
| [MKEAI](https://mkeai.com) | mixed | 支付寶/微信 | unverified | 社群論壇 + 中轉混合；主推 DeepSeek。 |
| [GPTGOD](https://gptgod.online) | reverse | 支付寶 | unverified | 逆向；便宜，穩定性無保證。 |
| [CloseAI](https://www.closeai-asia.com) | official-relay | 支付寶/微信/對公 | active | 自稱亞洲最大企業級中轉。 |

> **收錄 ≠ 推薦。** 收錄是為了記錄市場。打款或傳資料前請先走
> [評估清單](docs/evaluation.md)。

## 海外閘道與聚合平台

| 服務 | 類型 | 支付 | 備註 |
|---|---|---|---|
| [OpenRouter](https://openrouter.ai) | aggregator | 卡/加密貨幣 | 官方授權路由，加價約 5%；400+ 模型、60+ 供應商。ARR 據報約 $5M（2025-05）→ 約 $50M（2026 初）。 |
| [LiteLLM](https://litellm.ai) | gateway-oss | — | 開源閘道（100+ 供應商）+ 企業版。自架，自帶 Key。 |
| [Helicone](https://helicone.ai) | observability | — | LLM 可觀測性閘道；日誌/成本分析。 |
| [AIMLAPI](https://aimlapi.com) | aggregator | 卡/加密貨幣 | 400+ 模型，$20 起預付；支援加密貨幣暗示繞支付障礙。 |

## 對比與監控工具

| 工具 | 備註 |
|---|---|
| [中轉站競技場 (AI API PK)](https://www.aiapipk.com) | 約 40 家站點的 OpenAI / 逆向 / Claude / DeepSeek 報價牆。 |
| [awesome-ai-proxy (mn-api)](https://github.com/mn-api/awesome-ai-proxy) | 最早的清單（約 31 家）。**2026 年起已停更** —— 本倉庫延續這項工作。 |

## 如何安全地挑選

完整框架見 **[docs/evaluation.md](docs/evaluation.md)**。速覽：

1. **先看通道類型** —— `official-relay` > `mixed` > `aggregator` > `reverse`。
2. **做 canary 測試** —— 用已知難題，官方 vs 中轉，每週比對，識別偷偷降智。
3. **小額充值** —— 中轉站基本都是預付，絕不大額預存。
4. **按場景匹配** —— 敏感/合規資料走官方 API 或自架 `gateway-oss`，絕不用 `reverse`。

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
