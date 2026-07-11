# sidejob-ledger ブランチ

副業パイプライン（`docs/designs/22-side-job-automation.md`）の実運用データ専用ブランチ。`hermes-relay` ブランチと同じパターン: 実データ（案件台帳・提案文下書き・実行監査ログ・拡張候補分析）を、機能ブランチ（将来 `main` にマージされる）から隔離するために存在する。

- 構造（スキーマ・テンプレート・選別基準）は機能ブランチの `sidejob/config.md` / `sidejob/templates/` / `sidejob/fixtures/` / `sidejob/SETUP.md` が正
- ループの手順は機能ブランチの `loops/sidejob-*/CONTRACT.md` が正
- このブランチには**実データのみ**を置く。`main` にマージしない

## ファイル

```
sidejob/
├── pipeline-state.md       # 案件台帳（唯一の進捗ファイル）
├── proposals/              # 提案文下書き（YYYY-MM-DD-<id>.md）
├── work/                   # 案件ごとの制作ディレクトリ
├── receipts/               # 実行監査ログ（YYYY-MM-DD.md、追記専用）
└── expansion-candidates.md # 拡張候補ログ（追記専用）
```

読み書きは `loops/sidejob-intake/CONTRACT.md`「データの読み書き手順」節の手順に従う（このブランチを worktree で開いて操作し、変更後にコミット・pushする）。
