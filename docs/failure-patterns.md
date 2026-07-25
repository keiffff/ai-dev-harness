# Failure Patterns

AI agent の失敗を、プロジェクト固有のログではなく、再利用できる失敗パターンとして記録する。

## 仕様補完

未入力の事業文脈や既存契約を、agent がもっともらしい仕様として補完する。

対策:
- OpenSpec や design doc に判断を残す
- I/F、永続化、外部挙動の変更は止める
- 互換性や fallback は必要性を確認してから入れる

## 過剰防御

不要な fallback、backward compatibility、retry、default 値、wrapper を追加する。

対策:
- 既存データ、API、テスト、運用で必要な互換性かを確認する
- 未リリースの中間状態には互換性を持たせない
- 新しい抽象は所有責務と呼び出し側の簡素化を説明できる場合だけ追加する

## 意味の薄いテスト

修正後に不要になった挙動を「しないこと」テストとして残す、または mock の相互作用だけを検証する。

対策:
- テストが守る契約を言語化する
- public contract、incident recurrence、security/cost risk を守らない negative test は増やさない
- 既存テストの削除や緩和は、何を保証していたかを確認してから行う

## 文章として自然な誤報

根拠が薄い原因推定を、運用報告として自然な文章に整えてしまう。

対策:
- 観測事実、推測、未確認事項、暫定対応、恒久対応を分ける
- 外部サービス障害や「コードでは直せない」を断定する前に、公式status、ログ、設定、再現条件を確認する

## 共有環境でのインフラ破壊

一時的な検証環境では成功した CDK 変更が、共有環境や本番相当環境で固定名、Export、既存リソース、quota、region、VPC 不整合により失敗する。

対策:
- CDK design review で resource owner、physical name、Export、environment separation、region/VPC、quota、post-deploy boundary を確認する
- deploy は agent から実行しない
