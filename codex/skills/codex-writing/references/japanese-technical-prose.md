# Japanese Technical Prose Examples

Read only the section matching the requested deliverable or wording problem. The examples below are invented, generic illustrations, not excerpts from user conversations or evidence for a real project. Use task-supplied facts in actual writing. These examples demonstrate reader needs, information order and voice rather than a mandatory document structure.

## Slack: Share a Change and Its Measured Effect

Input: A search improvement is live. In a test using the same 1,000 records, median response time changed from 900 ms to 300 ms. The result does not measure production response time. Search results are unchanged. Share with the team; no action is requested.

Complete draft:

- 検索の待ち時間を短縮する変更を反映済み。検索結果は変わらない
  - 同じ1,000件を使ったテストでは、応答時間の中央値が900msから300msに短縮
  - 本番環境での応答時間は未計測

The main change is the parent item; the measured effect and its scope are children. The comparison gives the numbers meaning. Do not append an approval request or follow-up commitment absent from the input.

## Technical Explanation: Introduce the Mechanism Before Its Details

Input: Explain cursor pagination to someone who knows that a screen lists records but does not know the term. The API returns a token identifying where the current page ended; the next request supplies it to continue. No ordering or consistency guarantees are supplied.

Complete explanation:

一覧を少しずつ取得するときに、前回の続きから取得する方法を「カーソル方式」と呼ぶ。

APIは一覧の一部と、その末尾を示すトークンを返す。次のリクエストにこのトークンを渡すと、続きの一覧を取得できる。画面側はトークンを保持し、「次へ」を押したときに送信する。

The opening connects an unfamiliar term to the reader's existing task. Explain only the supplied mechanism; do not invent guarantees or add implementation internals the reader does not need.

## Wording: Make the Actual Behavior Understandable

| Avoid | Prefer |
| --- | --- |
| この変更で整合性を改善する | ファイルを作成してから公開状態を更新し、公開済みなのに再生できない状態を避ける |
| メタ情報を反映する | 取得元の名前をレスポンスに含める |
| 既存と同じ扱いにする | フィールドが欠けている場合は、既存クライアントと同じく未設定として扱う |
| 同一の対象へ適用する | IDが一致するレコードへ適用する |

Keep actual source facts and requested meaning. Do not invent the mechanism just to make a sentence sound concrete.
