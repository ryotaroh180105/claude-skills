# asset-research

自分専用の資産運用分析エンジン。詳細設計は
[`docs/designs/23-asset-research-engine.md`](../../../../docs/designs/23-asset-research-engine.md)、
使い方は [`SKILL.md`](SKILL.md) が正。

## 前提条件（初回のみ）

| # | やること | 発行/作成先 | 所要時間 |
|---|---|---|---|
| 1 | FRED APIキー発行 | https://fred.stlouisfed.org/docs/api/api_key.html | 2分（無料） |
| 2 | e-Stat アプリケーションID発行 | https://www.e-stat.go.jp/api/ | 5分（無料・要利用登録） |
| 3 | EDINET Subscription-Key発行 | https://api.edinet-fsa.go.jp/ | 5分（無料・要利用登録） |
| 4 | private リポジトリ `invest-journal` を作成 | 自分のGitHubアカウント | 1分 |
| 5（任意） | `anthropics/financial-services` の `model-builder` プラグイン導入 | `/plugin marketplace add anthropics/financial-services` → `/plugin install model-builder@financial-services` | 3分 |

キーは `~/.asset-research/.env` に書くか、セッションの環境変数に設定する。
**このリポジトリにも invest-journal にもキーをコミットしない。**

```bash
# ~/.asset-research/.env の例
FRED_API_KEY=xxxx
ESTAT_APP_ID=xxxx
EDINET_SUBSCRIPTION_KEY=xxxx
```

## セットアップ確認

```bash
pip install -r requirements.txt
python scripts/fetch_macro.py --dashboard
```

キー未設定の指標は `未検証（FETCH_FAILED: ...）` と表示される（無言で失敗しない）。

## テスト

```bash
python -m pytest tests/ -q
```

fetcherはネットワークをモックしているため、APIキーなしで実行できる（61 tests, 2026-07-11時点）。

## 出口（アンインストール）

- `plugins/asset-research/` ディレクトリを削除するだけでよい。
- `invest-journal` private リポジトリは別管理のため、そのまま残る（データの持ち出し方は
  そのリポジトリをclone/exportするだけ）。

## 期待値（保証範囲）

- 数値の正しさは元データ提供元（FRED/e-Stat/EDINET/EDGAR/yfinance/stooq）に依存する。
  本スキルは出典付与・2系統突合・異常検知を行うが、完全な正確性は保証しない。
  重要な判断の前に公表資料との突合を推奨する（`docs/designs/23-asset-research-engine.md` §4, §8）。
- 投資助言ではない。売買判断の最終責任はユーザーにある。

## フィードバック窓口

このセッション（Claude Code）に直接伝える。バグ・改善要望は `docs/designs/23-asset-research-engine.md`
の未解決事項またはMISTAKES.mdに記録して継続する。
