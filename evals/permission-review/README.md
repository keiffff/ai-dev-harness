# Permission review policy evaluation

この評価は、常時実行されるPermissionRequest hookとは分けて実行します。しきい値を変更する前に、現在値と候補値を同じJevのスコアへ適用し、calibrationとholdoutのfalse allow、false defer、selection rateを比較します。候補の採用やしきい値の自動変更は行いません。

`JEV_KIT_ROOT`には、build済みのjev-kit checkoutを指定します。API keyは通常のpermission reviewと同じく`keychain-env-exec`から渡します。

```bash
JEV_KIT_ROOT=/absolute/path/to/jev-kit \
  /absolute/path/to/keychain-env-exec TYPESAFE_API_KEY JEV_PERMISSION_REVIEW_API_KEY -- \
  node evals/permission-review/evaluate.mjs
```

`--candidate`の値は、`id=policyCompliant,instructionAligned,highRisk`の順です。複数指定できます。候補を省略すると、現在のpolicyだけをcalibrationとholdoutで評価します。

- `calibration.json`: policy候補を組み立てるための既知ケース
- `holdout.json`: calibrationに使わず、候補が別のケースでも成立するか確認するケース
- `hooks/codex/jev-permission-review-policy.json`: 現在運用しているbaseline policy

fixtureの期待値は人間が決めます。出力は比較材料であり、候補を自動採用しません。
