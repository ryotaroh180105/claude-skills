---
id: 20260708T135636Z-note-automation
engine: hermes
status: ok
executed_at: 2026-07-08T13:59:32Z
duration_seconds: 94
---

**1. 公式API有無（出典URL）**  
note公式ヘルプ（2025年5月8日更新）：「現在、noteが公式で公開しているAPIはありません。また、今後の公開予定や公開の可能性につきましても、現時点では未定となっております。」  
https://www.help-note.com/hc/ja/articles/46643492548121-note%E3%81%8C%E5%85%AC%E5%BC%8F%E3%81%A7%E5%85%AC%E9%96%8B%E3%81%97%E3%81%A6%E3%81%84%E3%82%8BAPI%E3%81%AF%E3%81%82%E3%82%8A%E3%81%BE%E3%81%99%E3%81%8B  
複数のnote記事でこの公式ヘルプが引用されており、記事投稿用・下書き作成用の公式パブリックAPIは存在しないと明記されている。  
https://note.com/kawayasblog/n/n2fa8bfee9e3d  
https://note.com/jibun_updating/n/nd2eb96ca6255

**2. 非公式の自動投稿手段とリスク（規約・BAN事例、出典URL）**  
公式APIが存在しないため、ブラウザ開発者ツールで内部通信を解析し、非公式エンドポイント（例: POST /api/v1/text_notes、POST /api/v1/text_notes/draft_save）を利用した事例が複数報告されている。PlaywrightやCookieベースのログインによるブラウザ自動化、または直接APIコールで下書き作成までを実現した例あり。GitHub上の専用OSSライブラリは検索結果に確認されず、主に個人note記事での実装共有。  
https://note.com/soundsfun2010/n/n0f24a1c23358  
https://note.com/a_g_e_n_t_b_o_t/n/n86da8314430b  
https://note.com/gentle_prawn80/n/n535624add56f  
https://note.com/jibun_updating/n/nd2eb96ca6255  

リスク：noteご利用規約で「不正な手段によるアクセス」や「サーバーへの過度な負担をかける行為」が禁止されており、非公式API/スクレイピングは規約抵触の可能性あり。仕様変更で突然動作しなくなる、またはアカウント停止（BAN）のリスクが指摘されている。具体的なBAN事例の詳細は確認されず、「自己責任」「非推奨」との警告が複数ある。  
https://note.com/kawayasblog/n/n2fa8bfee9e3d  
https://note.com/eplab/n/n9e77c7ecee3e  
https://note.com/furokun/n/n8dd33b6e5ff8  
https://terms.help-note.com/hc/ja/articles/44943817565465-note-%E3%81%94%E5%88%A9%E7%94%A8%E8%A6%8F%E7%B4%84

**3. 公式に許可された自動化連携（出典URL）**  
noteへの投稿・下書き作成に関するZapier、Make.com、IFTTT、RSS自動投稿の公式連携は確認されなかった。RSSはnote記事公開後の「表示自動化」（自サイトへの埋め込みや通知用）として公式ヘルプで案内されているが、noteへの投稿手段ではない。  
https://www.help-note.com/hc/ja/articles/4402395202841-iframe-RSS%E3%81%A7-%E8%87%AA%E5%88%86%E3%81%AE%E3%82%B5%E3%82%A4%E3%83%88%E3%81%ABnote%E3%82%92%E8%A1%A8%E7%A4%BA%E3%81%99%E3%82%8B  
https://note.com/kawayasblog/n/n2fa8bfee9e3d

**4. 実務でのワークフロー例（出典URL）**  
公式APIがないため「下書き作成の半自動化＋手動公開」が実務で推奨・実施されている事例多数。  
具体例：ObsidianなどのMarkdown原稿をHTML変換 → Cookie認証で非公式下書きエンドポイントへPOST（draft作成） → note上で画像選択・最終調整・手動公開。  
理由：見出し画像の判断、Markdown変換の微調整、公開タイミングの人間判断を残すため。完全に自動化せず「下書きまで自動・公開は手動」が安定運用として機能。  
https://note.com/jibun_updating/n/nd2eb96ca6255  
https://note.com/kawayasblog/n/n2fa8bfee9e3d

**5. 未確認・断定できない点**  
- 具体的なアカウントBAN事例の有無・詳細（リスク指摘のみで実例なし）。  
- GitHub上の公開OSSライブラリやPlaywright/Puppeteerの具体的なリポジトリ事例（note記事内での言及はあるが、直接のリンク・コード確認なし）。  
- 最新のnoteご利用規約における自動化禁止条項の正確な文言解釈（複数記事で「公式APIがない場合の自動化はNG」と解釈されているが、公式文言の全文確認は限定的）。  
- note Pro特有のAPI機能の有無（検索で該当情報なし）。

**6. 使用ツール名一覧**  
web_search  
open_page
