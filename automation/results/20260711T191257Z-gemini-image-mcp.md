---
id: 20260711T191257Z-gemini-image-mcp
status: ok
executed_at: 2026-07-11T19:13:53Z
duration_seconds: 38
---

**1. 該当MCPサーバー一覧（名称/GitHub URL/インストールコマンド、出典URL）**

- shinpr/mcp-image (https://github.com/shinpr/mcp-image, 約134-136 stars)  
  インストール: `claude mcp add mcp-image --env GEMINI_API_KEY=your-api-key --env IMAGE_OUTPUT_DIR=/absolute/path/to/images -- npx -y mcp-image`  
  出典: [web:2], [web:1], [web:23], [web:77], [web:79]

- @houtini/gemini-mcp (https://github.com/houtini-ai/gemini-mcp, 27 stars; npm @houtini/gemini-mcp)  
  インストール: `claude mcp add gemini-mcp -s user -- npx -y @houtini/gemini-mcp` (または `-e GEMINI_API_KEY=...`)  
  出典: [web:7], [web:32], [web:41]

- @jimothy-snicket/gemini-image-mcp (npm @jimothy-snicket/gemini-image-mcp; GitHub JimothySnicket/gemini-image-mcp)  
  インストール: `npx -y @jimothy-snicket/gemini-image-mcp` (claude mcp add 経由、GEMINI_API_KEY env)  
  出典: [web:0], [web:61], [web:63]

- sanxfxteam/gemini-mcp-server (https://github.com/sanxfxteam/gemini-mcp-server, 5 stars; npm gemini-mcp-server)  
  インストール: npx -y gemini-mcp-server または github: 参照 (claude mcp add 経由)  
  出典: [web:5], [web:18], [web:50], [web:66]

- その他関連:  
  - rlabs-inc/gemini-mcp (https://github.com/rlabs-inc/gemini-mcp): `claude mcp add gemini -s user --env GEMINI_API_KEY=YOUR_KEY npx -y @rlabs-inc/gemini-mcp`  
    出典: [web:15], [web:33]  
  - falahgs/imagen-3.0-generate-google-mcp-server (Imagen 3.0 特化)  
    出典: [web:11], [web:68]  
  - lansespirit/image-gen-mcp (63 stars, Imagen 4/3 対応)  
    出典: [web:72], [web:81]  
  - writingmate/imagegen-mcp, cxoagi/gemini-media-mcp (Imagen 4 / Gemini image 対応)  
    出典: [web:69], [web:73]

主に npx ベースで `claude mcp add` 対応。Gemini 2.x (Nano Banana / 2.5 Flash Image) や Imagen 3/4 を MCP ツールとして公開。

**2. 必要な認証・料金（出典URL）**

- Google AI Studio の API キー (GEMINI_API_KEY env) 必須。  
  取得: https://aistudio.google.com/apikey  
  無料枠: 単一ユーザーで十分にカバー（基本無料）。  
  出典: [web:7], [web:4], [web:1]

**3. 実利用レビュー・実例（出典URL）**

- dev.to 記事: Gemini 2.5 Flash Image (Nano Banana) を使った MCP サーバー構築・Claude Code への追加例。画像生成・編集・ローカル保存（IMAGE_OUTPUT_DIR）を実装・動作確認。  
  出典: [web:1], [web:23]  
- YouTube: Claude Desktop に @jimothy-snicket/gemini-image-mcp を追加し、Gemini Nano で画像生成・編集を有効化するデモ。  
  出典: [web:0]  
- houtini ブログ: @houtini/gemini-mcp で Claude Code/Desktop から画像生成。Google AI Studio キー使用例と設定手順。  
  出典: [web:7]  
- 複数ソースで Claude Code から MCP ツール経由の画像ファイル生成・保存が確認可能（env で出力ディレクトリ指定）。  
  出典: [web:2], [web:12], [web:4]

**4. 未確認・断定できない点**

- 公式 Google/Anthropic 提供の MCP サーバーは検索結果に確認できず（すべてコミュニティ/OSS）。  
- 具体的なスター数変動や最新メンテナンス状況、すべてのサーバーでの Imagen 4 vs gemini-2.x 画像出力の詳細挙動。  
- 実際の Claude Code 呼び出し時の成功率・レート制限のユーザー体験（ソースに限定的な実例のみ）。

**5. 使用ツール名一覧**  
web_search
