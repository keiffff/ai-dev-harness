# Agent Architecture

この構成は、main agent に判断を集約し、周辺の skills、subagents、advisors、execution harness で支える。

## 中心

Sol main agent / Codex が repo 文脈、実装、差分確認、テスト確認、最終判断を持つ。

subagent や advisor は補助であり、最終判断、I/F判断、互換性判断、fallback判断、Git操作は main agent に残す。

外部情報源に強い research scout も同じ境界で扱う。scout は最新情報と直接URLを集めるが、一次情報の確認、repo 文脈への適用、最終判断は main agent に残す。

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
