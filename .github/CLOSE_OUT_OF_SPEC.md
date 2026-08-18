# Close comment — out-of-spec contribution

Use when closing a PR/issue that does not follow contribution rules.
Paste as the PR/issue comment, then close.

---

## English + 中文 (default)

```markdown
Thanks for the submission — closing this one as **out of spec** so the queue stays reviewable.

### Why
- {{REASON}}

This catalogue is **agent-maintained data**, not a free-form awesome-list paste.
Hand-edited READMEs, marketing copy, affiliate/UTM links, or `status: active` self-claims are rejected by policy + CI.

### How to resubmit the right way (agent-first)

**Read once, then act:**
1. Playbook: https://github.com/howardpen9/awesome-ai-api-proxy/blob/main/docs/agent-contribute.md
2. Schema: https://github.com/howardpen9/awesome-ai-api-proxy/blob/main/data/schema.md
3. Entrypoint for agents: https://github.com/howardpen9/awesome-ai-api-proxy/blob/main/llms.txt

**Quick rules:**
- Edit **`data/providers.yaml` only** (never the generated README tables).
- Plain `https://` URL — no `utm_*` / `ref=` / affiliate params.
- New entries: `status: unverified` (never self-claim `active`).
- If you operate the station: open an **Issue** with the new-provider template, or PR with `risk_flags: [operator_submitted]`.
- `notes`: one factual sentence, no marketing.
- Local check: `python -m scripts.validate` must exit 0.

**Operator / 运营方:** prefer Issue  
https://github.com/howardpen9/awesome-ai-api-proxy/issues/new?template=new-provider.yml

**Prices only:**  
https://github.com/howardpen9/awesome-ai-api-proxy/issues/new?template=submit-prices.yml

---

感谢提交。此 PR/Issue **不符合仓库规范**，先关闭以保持 review 队列干净。

### 原因
- {{REASON_ZH}}

本仓库是 **给 AI agent 维护的结构化目录**，不是随便改 README 的 awesome list。
手改 README 表格、营销文案、推广/UTM 链接、自标 `status: active` 都会被政策与 CI 拒绝。

### 正确重提方式（agent 本位）

请先读：
1. https://github.com/howardpen9/awesome-ai-api-proxy/blob/main/docs/agent-contribute.md
2. https://github.com/howardpen9/awesome-ai-api-proxy/blob/main/data/schema.md
3. https://github.com/howardpen9/awesome-ai-api-proxy/blob/main/llms.txt

要点：只改 `data/providers.yaml`；HTTPS 无 UTM；新条目 `unverified`；运营方自提加 `risk_flags: [operator_submitted]` 或开 Issue；`notes` 一句事实；本地 `python -m scripts.validate` 通过后再开 PR。

欢迎按文档用 AI agent 重新提交。谢谢理解。
```

### Reason snippets

| Code | EN | ZH |
|---|---|---|
| `readme` | Hand-edited generated README tables | 直接修改了自动生成的 README 表格 |
| `utm` | URL contains tracking/affiliate query params | URL 含 UTM/推广参数 |
| `active` | Claimed `status: active` without maintainer verification | 未经验证自标 `status: active` |
| `marketing` | Marketing / superlative language in notes or title | notes/标题含营销或夸张用语 |
| `dup` | Duplicate of an existing entry or open PR | 与现有条目或 open PR 重复 |
| `section` | Wrong YAML section / corrupted unrelated entries | 放错 section 或破坏了其他条目 |
| `operator` | Operator self-submission without disclosure flags | 运营方自提未标注 `operator_submitted` |
| `encoding` | Diff corrupts existing Unicode / unrelated rows | diff 破坏既有中文或其他条目 |
| `blank` | Blank / free-form issue — did not use a required form | 空白或自由发挥 issue，未使用必填表单 |

Replace `{{REASON}}` / `{{REASON_ZH}}` with one or more lines from the table.
