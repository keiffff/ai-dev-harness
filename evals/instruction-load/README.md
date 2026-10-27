# 指示変更と通常作業の比較

共通指示を増減したとき、特定の回帰例だけでなく、小さな通常作業の成果と作業量がどう変わるかを調べる任意の評価。全タスクで実行する必須チェックではない。

code・会話形式の引継ぎ・文章・データはすべて架空の標本であり、実会話、顧客情報、実プロジェクトの運用前提は含まない。既知の途中終了と停止は隣の`task-continuity/daily_totals.py`の標本・実行検査を再利用する。

| case | 成果物で確認すること |
| --- | --- |
| continuation | 原因質問の後も通常CLIを修正し、実CSVを生成。別入力・UTC省略・日付境界・夏時間・空入力を検査 |
| label | 指定した表示だけ変更し、他の既存内容を維持 |
| serialization | 整数への修正、id・キー省略・null・空文字・余分なキーの扱いを維持 |
| wording | 指定語句だけ変えた完成文を返し、元ファイルは維持 |
| investigation | 原因調査中、追加ファイル・cacheを含めて変更しない |
| stop | 明示停止後、追加ファイル・cacheを含めて変更しない |

## 実行

repository rootから、通常設定・認証の既存Codex CLIで実行する。PATHに正しい本体があれば`--codex-bin codex`を指定できる。各呼出しが1つの新規タスクとなり、モデル利用が発生する。

```sh
python3 evals/instruction-load/evaluate.py --output-dir tmp/instruction-load --label current --case label --codex-bin codex
```

依頼文・初期ファイルhash・native trace・stderr・最終回答・実成果の検査結果を出力先へ保存する。上の例は既存の.gitignoreで除外されるtmp/配下を使う。結果のコマンド実行数、編集イベント数、native usageは作業量の観測であり、それだけで品質向上を判定しない。traceと回答はローカルの実行結果であり、共有repositoryへ追加しない。

`--label`は結果の識別だけに使い、担当タスクのディレクトリ名や依頼文へ入れない。`--record-instruction-file`を繰り返し指定すると、手元の指示ファイルのhashと文字数だけを記録できる。このオプションは指示を配信・切替せず、指示本文も複製しない。

この評価器は共通指示・skill・runtime・設定・認証を変更しない。labelだけを変えても新旧比較にならない。実際に使った版と配信を別途確認し、同じ入力、判定器、モデル、推論設定、権限で比較する。指示量の割合はAGENTS単体と実配信全体を区別する。内容と長さを同時に変えた比較から、長さだけの因果効果を主張しない。

## 判定と限界

`artifact_checks_pass`は実ファイル・別プロセスの実行・原文照合の結果。`pass`はnativeの終了コード0と実回答の存在も必要とする。起動前の失敗、回答なし、未修正、ハードコードした正解を成功にしない。

`answer_link_checks`は、この6題材の最終回答が実在するworkspaceファイルへ相対リンクを張っていないかを別に記録する。外部URLや章アンカーは対象外。コード中の行参照や原文のコピーを、ファイルリンクと取り違えない。成果物の機能判定を上書きせず、出力上の不備を隠さないための観測である。

continuationの原因説明、investigationの原因説明、stopの未達説明は、成果物検査だけでは正しさを確定できない。自動検査が通っても`pass: null`として、元コード・引継ぎ・実回答の照合事項を`manual_review`に返す。説明を読まずに合格へ変えない。終了コードは完全な自動合格で0、それ以外は1で、手動確認待ちと失敗はJSONで区別する。手動判定は結果JSONを上書きせず別記録へ残す。

両条件が合格しても品質向上とは言わない。短い合成例の成功を長い実会話や実製品の保証にしない。判定器自体の故障注入は`tests/test_instruction_load_eval.py`、再利用するCSV判定は`tests/test_daily_totals_eval.py`。

## 私的な実会話を再生する

同じ観測と比較を実会話にも使う入口は`replay.py`。既に監査した、問題直前で切ったnative sessionのseedを使う。会話抽出や採点基準の作成をモデルへ任せず、未来の訂正、toolの生出力、credentialを含めないことを準備側で確認する。共有repoには実会話、seed、案件の識別子や運用前提を置かない。ケース、rubric、snapshot、結果は私的保存先を指定する。

ケースJSONは`id`、`request_file`、`scope_file`、`seed_file`、`session_id`、`rubric_file`、`model`、`reasoning`を持つ。ファイルパスはケースJSONの場所から解決する。`files_dir`を指定すれば必要な初期ファイルを作業場所へコピーする。snapshotは変更対象のskillだけを格納する。対象skillのユーザー側登録をその実行内で無効にし、作業場所の`.agents/skills`へsnapshotを配信する。他の設定・認証・hookは維持する。歴史的なファイルが必要なケースは利用可能な初期ファイルを用意し、欠けたまま技術的正しさを合格にしない。

```sh
python3 evals/instruction-load/replay.py run --case-file "$CASE_FILE" --skills-root "$SKILL_SNAPSHOT" --output-dir "$PRIVATE_RESULTS" --codex-bin "$CODEX_BIN" --label "$CONDITION"
```

条件名、採点基準、case manifestをactorの依頼文や作業ディレクトリ名に入れない。rubricはhashのみ実行記録に残す。これはOSの読取制限ではないため、採点や別試行の参照がなかったかtraceも確認する。既存runtimeが外側sandboxで起動できない場合はsetup失敗として保存する。実際の認証・権限拒否を別経路で迂回しない。

rubricの`checks`は重複しない`id`と`description`。回答後の判定ファイルは`artifacts`（result.jsonと同じhash辞書）、manifestと同じ`rubric_sha256`、全criteriaに対応する`checks`を持つ。各checkに`id`、`verdict`（pass/fail/unknown）、`reason`、`evidence`（記録されたfileとその中の正確なquoteの配列）を記入する。引用の一致は根拠の所在確認であり、意味の採点の正しさは別に確認する。

```sh
python3 evals/instruction-load/replay.py compare --before "$BEFORE_RUN" --after "$AFTER_RUN" --before-assessment "$BEFORE_ASSESSMENT" --after-assessment "$AFTER_ASSESSMENT" --rubric-file "$RUBRIC_FILE" --output "$PRIVATE_COMPARISON"
```

入力、scope、seed、初期ファイル、モデル、推論設定、rubricが異なる組は比較を拒否する。出力改変、skill snapshotの変更、判定漏れ、存在しない引用を合格にしない。判定未実施・unknownは合格にせず、native起動失敗や回答なしは別に記録する。比較JSONには実回答・保存稿・使用量・時間・コマンド数を残す。`stages`には依頼理解、入口、手順、成果のどこで失敗したかを判定根拠とともに記録できる。`human_corrections`は実際に観測した場合だけ記録し、再生評価の失敗数から人間の訂正回数を捏造しない。

失敗例と正常例を同じ候補で確認し、未解決・回帰も残す。単発比較を成功率にせず、使用量から料金を推測しない。既存結果の再採点と、新しい候補の実行を区別する。これは任意の改善評価であり、通常タスクごとの必須実行やStop hookではない。故障注入は`tests/test_private_replay_eval.py`。

複数件の採否確認は`suite`でまとめる。事前に選んだcase ID一覧を`{"cases": [...]}`として私的に保存し、planの`comparisons`へ各件の`case`とcompareに渡す5つのpathを指定する。宣言した件の欠落・重複、ケース違い、同一条件での異なるskill snapshotの混在を拒否する。別候補から成功例だけを寄せ集めない。

```sh
python3 evals/instruction-load/replay.py suite --case-list "$CASE_LIST" --plan-file "$COMPARISON_PLAN" --output "$PRIVATE_SUITE_RESULT"
```

結果に改善・回帰・未解決を別々に残す。未解決や判定保留がある場合は`adoption: not_ready`と終了コード1を返す。すべての対象基準を満たした場合も、返すのは`no_regression_observed`であり、一般的な改善効果や公開許可ではない。この判定は任意の評価コマンドに限定し、通常の回答やGit操作を新たに遮断しない。

## 共通指示から分けた責務

| 確かめる挙動 | 所有するコード・検証 |
| --- | --- |
| taskメモの保存・復元・更新・他taskとの分離 | 既存runtime hook、`tests/test_runtime_task_note.py`、`tests/test_runtime_task_note_storage.py` |
| helperの成功を通常入口の成功と取り違えない | CSVの通常CLIと別入力による実生成、`tests/test_daily_totals_eval.py` |
| 型・省略・null・空文字や文章の指定外部分を維持 | serialization・wording・labelの成果物検査 |
| 停止・調査中に勝手に編集しない | 全階層のファイルhash比較。cacheも含める |
| 実ファイルへのリンク形式 | `answer_link_checks`と既知の相対リンク不備の回帰テスト |
| 生CLI・秘密情報の表示・破壊的操作の代表例を止める | 既存policy hookと`tests/test_hooks_wrappers.py`のHookPolicyTests |

コードが担保する範囲と、agentの判断を分ける。hookは目的の達成やユーザーの操作許可を自動判定しない。元の成果、継続、明示停止、操作範囲、既存契約の短い共通指示は残す。Git公開の細かい手順は既存のcodex-git-publishが所有する。ここにある検証を毎回すべて実行させる指示や、新しいStop gateは追加しない。
