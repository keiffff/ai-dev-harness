# Agent Architecture

この構成は、main agent に判断を集約し、周辺の skills、subagents、advisors、execution harness で支える。

## 中心

Sol main agent / Codex が repo 文脈、実装、差分確認、テスト確認、最終判断を持つ。

subagent や advisor は補助であり、最終判断、I/F判断、互換性判断、fallback判断、Git操作は main agent に残す。

外部情報源に強い research scout も同じ境界で扱う。scout は最新情報と直接URLを集めるが、一次情報の確認、repo 文脈への適用、最終判断は main agent に残す。

## レビュー表現

main agent は、レビュー対象の内容だけでなく、人間が何を確認するかに合わせて表現を選ぶ。正確な比較には表、依存関係には graph、状態遷移や処理順序には flow、時間による変化には timeline、階層には tree を使う。複数の view や情報配置がレビューに必要な場合は、standalone HTML を使う。

視覚化は、判断や契約を記録した Markdown、OpenSpec、code、schema の代わりにはしない。生成 HTML は元の artifact から作る review projection として扱い、人間の指摘を main agent が元の artifact に反映してから再生成する。

## 人間の役割

人間は作業を細かく指示し続けるのではなく、AI が知らない文脈を与える。

- 目的
- 制約
- 事業文脈
- 仕様判断
- やらないこと
- 停止判断

## 介入を残す理由

AI agent は賢いため、足りない文脈をもっともらしく補完して進む。完全自動化すると、仕様の穴、既存契約、運用前提、レビュー粒度の判断が入る前に実装が進みすぎる。

この構成では、細かい作業は agent に任せる一方で、I/F、永続化、互換性、fallback、Git、cloud、secret、production では止まるようにする。
