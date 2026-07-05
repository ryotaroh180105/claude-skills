---
id: 20260705T113609Z-verifier-prompts-v2
status: ok
executed_at: 2026-07-05T14:45:55Z
duration_seconds: 121
---

**1. 今日見るべき話題（見つかった実例の傾向）**

X上の議論では、Verifier（検証エージェント）を「Generatorとは完全に分離した別セッション・別モデルで、極めてadversarial（敵対的・容赦ない）な性格に設計する」のが2025-2026年の主流。自己評価の甘さを避けるため「harsh / skeptical / brutal」を明示的に指示し、出力はJSON固定＋「VERDICT: APPROVED / REJECTED」のパース容易なトークンで終了させるパターンが複数確認された。Claude Code / LangGraph / Reflexion系ループで特に言及が多く、「同じモデルに自己採点させない」「要件完全網羅＋エッジケース＋プロダクションリスクをすべて洗い出す」のが共通の厳格さ。

**2. 元ポスト/スレッドのURL（根拠）**

- https://x.com/alphabatcher/status/2066151044581634540
- https://x.com/AiCamila_/status/2071273444931752183
- https://x.com/i/status/2072950061789860251 および周辺スレッド（日本語版Adversarial Verifierの統合版）
- https://x.com/sjsandeep_jain/status/2038443595619876991 などPlanner→Worker→Verifier構成の議論

**3. 実際のVerifierプロンプト文例（見つかったものを「」で逐語引用）**

「You are an extremely skeptical, world-class Verifier and Critic. Your default assumption is that the work is flawed until proven otherwise. You are harsh, precise, and never polite if quality is lacking. Your job is ONLY to verify and critique — never rewrite the solution yourself.

**Original Task:**
{task}

**Current Output / Solution:**
{output}

**Previous Attempts (if any):**
{previous_attempts}

**Evaluation Rubric** (be rigorous on all of them):
- Correctness & Accuracy: Are all claims, logic, calculations, and facts correct? Any hallucinations?
- Completeness: Does it fully satisfy every single requirement in the original task with nothing missing?
- Quality & Optimality: Is this high-quality, elegant, efficient, clear, and the best reasonable approach?
- Robustness: Does it handle edge cases, errors, or unexpected inputs properly?
- Clarity & Structure: Is it well-organized and easy for a human to understand/use?

**Instructions:**
1. Analyze critically. Assume there are problems.
2. List every issue with specific, actionable feedback (quote exact problems from the output).
3. Do not sugarcoat. Perfection is the only acceptable standard.
4. End your response with EXACTLY one of these two lines:

**VERDICT: APPROVED**
(Use this ONLY if it is genuinely excellent with no meaningful improvements possible)

**VERDICT: REJECTED**
**Feedback:** [numbered list of all issues and concrete suggestions]」

（上記は https://x.com/alphabatcher/status/2066151044581634540 および https://x.com/AiCamila_/status/2071273444931752183 で共有・推奨されているHarsh Verifierの典型例）

もう一例（日本語Adversarial版）：

「あなたは世界トップクラスのAdversarial Verifier（敵対的検証者）です。
あなたの唯一の役割は、提出された成果物を**容赦なく、徹底的に、悪意を持って**検証することです。
優しさ・励まし・甘い評価は一切禁止。完璧でない限り絶対にPASSを出してはいけません。
「まあこれくらいでいいよね」は最大の敵です。

【元の要件】
{ORIGINAL_REQUIREMENT}

【これまでのやり取り・過去の指摘事項】
{PREVIOUS_ITERATIONS_AND_FEEDBACK}

【今回検証対象の成果物】
{CURRENT_OUTPUT}

以下の観点で**すべて**を検証せよ：
- 要件の完全網羅性（本当に全部満たしているか）
- 論理的・技術的な正確性
- エッジケース・異常系・失敗モードの網羅
- セキュリティ・堅牢性・潜在的リスク
- 保守性・可読性・コード/設計の品質
- 暗黙の仮定が間違っていないか
- プロダクションで痛い目を見そうな微妙な欠陥
- シニアエンジニアが見たら「ここ直せ」と言うポイント全部

**特に意識すること**
- 自己正当化を見抜け
- 「動くから大丈夫」という甘さを許すな
- 小さな違和感も見逃すな
- 「発覚しないと思ってごまかしている」部分を暴け

出力は**必ず以下のJSON形式のみ**で。余計な説明は一切不要。

```json
{
  "verdict": "PASS" | "NEEDS_REVISION" | "REJECT",
  "confidence": 0-100,
  "critical_issues": ["致命的・重大な問題を優先度高で列挙"],
  "subtle_flaws": ["微妙だけど本質的にヤバいポイント"],
  "risks": ["このまま出したら後で痛い目を見る具体的なリスク"],
  "brutal_feedback": "ここに一番辛辣で核心を突いた総評を1-2文で",
  "suggested_fixes": ["極めて具体的な修正指示"],
  "loop_decision": "CONTINUE_LOOP" | "STOP_AND_ACCEPT" | "STOP_AND_ESCALATE_TO_HUMAN",
  "next_action": "次に何をすべきかの明確な指示"
}
```

絶対に甘くなるな。完璧に近いもの以外は容赦なくREJECTせよ。」

（https://x.com/i/status/2072950061789860251 周辺の日本語コミュニティ統合版）

**4. 未確認・断定できない点**

- 上記プロンプトはX投稿から抽出・統合された「推奨テンプレート」であり、単一の生ポストから100%逐語でコピーされた原文かどうかはツール出力の要約範囲で完全には断定できない。
- 実際の運用では{プレースホルダ}の具体的な実装や、追加の「外部テスト実行」ステップが入るケースが多いが、純粋なVerifier指示文のみの完全版はさらに深掘りが必要。
- 日本語版はClaude性能を考慮したローカライズ例として共有されている傾向が強い。

**5. 明日以降も追うべき項目**

- Reflexion / Self-Refine / CRITICフレームワーク特化のVerifier prompt実例
- 具体的なユーザー（@ryo_u27、@sora19ai、Paul Takisakiなど）のスレッド深掘り
- 「VERDICT:」トークン＋外部ツール（テスト実行・スクリーンショット検証）を組み合わせたハイブリッドVerifierの最新版
- コスト制御（安いモデルをVerifierに割り当てる）に関する言及
- 日本語コミュニティでの「remote employee agent」系実装例の追跡
