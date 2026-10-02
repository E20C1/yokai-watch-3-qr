# 日本語アイテム名の照合方針

このプロジェクトでは英語名を機械翻訳せず、日本版『妖怪ウォッチ3』Ver.4.0で使われる名称を主表示にします。

## 照合方法

1. `QR2_INFO` に格納されている Item ID を基準にする。
2. YKW Modding の YW3 Item ID 資料で、ハッシュ化された Item ID と英語版の項目を確認する。
3. 日本版 Ver.4.0 の公開ゲームデータ表（どうぐ / そうび / たいせつ）と項目順・カテゴリ・内容を照合し、日本版名称を確定する。
4. 日本語名を主表示、英語名を検索用エイリアスとして保持する。
5. 根拠を確定できない ID は推測で命名せず、Hex ID のまま扱う。

## 参照先

- とげにゃん「妖怪ウォッチ3 どうぐ一覧」Ver.4.0
  - https://togenyanweb.appspot.com/Yokai/yw3/CONSUME_latest.html
- とげにゃん「妖怪ウォッチ3 そうび一覧」Ver.4.0
  - https://togenyanweb.appspot.com/Yokai/yw3/EQUIPMENT_latest.html
- とげにゃん「妖怪ウォッチ3 たいせつ一覧」Ver.4.0
  - https://togenyanweb.appspot.com/Yokai/yw3/IMPORTANT_latest.html
- YKW Modding `YW3 Item IDs`
  - https://ykw-modding.github.io/yo-docs/modding-resources/item-ids/YW3ItemIDs.html

この名称表はゲーム本体ファイルそのものを配布するものではありません。
