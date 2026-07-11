---
id: 20260711T191257Z-openai-image-mcp
status: ok
executed_at: 2026-07-11T19:14:25Z
duration_seconds: 32
---

**1. 该当MCPサーバー一覧（名称/GitHub URL/インストールコマンド、出典URL）**

- **SureScaleAI/openai-gpt-image-mcp**（https://github.com/SureScaleAI/openai-gpt-image-mcp）：GPT-4o/gpt-image-1対応の画像生成・編集MCPサーバー。Node.js製。インストール：git clone後yarn install、yarn buildでdist/index.jsを生成。Claude設定例：`"command": "node", "args": ["/absolute/path/to/dist/index.js"], "env": {"OPENAI_API_KEY": "sk-..."}`。出典：[web:29]、[web:30]、[web:21]。
- **labeveryday/gpt-image-mcp**（https://github.com/labeveryday/gpt-image-mcp）：gpt-image-1による生成・編集・分析対応。Python/FastMCP製。インストール：git clone、uv sync。Claude設定例：`"command": "uv", "args": ["run", "gpt-image-mcp"], "cwd": "/path/to/gpt-image-mcp"`。Claude Code向け設計。出典：[web:2]、[web:27]、[web:33]。
- **Garoth/dalle-mcp**（https://github.com/Garoth/dalle-mcp）：DALL-E 2/3対応（生成・編集・バリエーション）。出典：[web:15]、[web:18]。
- **jerryzhao173985/openai-image-gen-mcp**（https://github.com/jerryzhao173985/openai-image-gen-mcp）：gpt-image-1生成・編集。Node.js、run-with-key.shやstart.sh使用、またはOPENAI_API_KEY設定でbuild/index.js。出典：[web:7]、[web:10]。
- **@singularity2045/image-generator-mcp-server**（npm）：gpt-image-1.5対応、テキストプロンプトで画像生成・ローカル保存。npx経由でClaude Desktop/Cursor対応。出典：[web:12]。
- その他：lansespirit/image-gen-mcp（https://github.com/lansespirit/image-gen-mcp、63 stars、gpt-image-1対応）、image-mcp（npx image-mcp@latest + OPENAI_API_KEY）。出典：[web:40]、[web:23]。

claude mcp addコマンドの直接例は限定的で、主にclaude_desktop_config.jsonやCursor/VSCode設定、またはHTTP/SSE用claude mcp add --transport http/sseの一般形式。出典：[web:59]。

**2. 必要な認証・料金（出典URL）**

- 認証：OPENAI_API_KEY環境変数必須。platform.openai.comでAPIキー取得（課金アカウント必要、gpt-image-1/DALL-Eアクセス有効化）。出典：[web:2]、[web:21]、[web:23]。
- 料金（gpt-image-1目安、2026年時点）：品質・解像度による（1024×1024など）。Low $0.011前後、Medium $0.042前後、High $0.167前後/枚（Mini版はさらに安価$0.005〜）。DALL-E 3は旧来$0.04程度だったがAPIから削除傾向。トークンベース課金（入力/出力トークン）も適用される場合あり。出典：[web:47]、[web:49]、[web:50]、[web:52]。

**3. 実利用レビュー・実例（出典URL）**

- GitHubリポジトリ内で「Claude Code」「Claude Desktop」で自然言語指示（「generate an image of...」）によりMCPツール呼び出し可能と記載。画像生成・編集・ローカル保存例あり（npm版はfilesystem保存明記）。ClaudeにMCP設定追加後、ツールとして利用可能。出典：[web:2]、[web:12]、[web:27]。
- レジストリ（mcpservers.org、mcpmarket.com）でClaude/Cursor/VSCode/Windsurf対応と記載、画像生成ツールとして統合例。出典：[web:1]、[web:5]。
- 実際のClaude Codeエージェント呼び出し実例として、プロンプトで画像生成・保存が機能するとリポジトリ/レジストリで言及。出典：[web:7]、[web:10]。

**4. 未確認・断定できない点**

- すべてのサーバーで`claude mcp add`のワンコマンド直接追加の公式サポート確認（主に手動JSON設定またはnpx）。
- 各リポジトリの最新スター数・アクティブメンテナンス状況の変動。
- 具体的なClaude Codeユーザーによる大量実運用レビューや失敗事例の詳細（リポジトリ記載の主張が主）。
- OpenAI公式MCPサーバーの存在（すべてOSS/サードパーティ）。
- 最新のgpt-image-1.5/2対応状況や保存ファイル形式の完全性。

**5. 使用ツール名一覧**  
web_search（複数回）
