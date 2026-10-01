# YW3 QR Lab

『妖怪ウォッチ3 スキヤキ』日本版 Ver.4.0 の `QR2_INFO` をブラウザ上で検索・生成・解析するための静的Webアプリです。

## Features

- JP Ver.4.0 `QR2_INFO` **2,143件**を検索
- Item ID / Type / Flag / RandomQRTable から絞り込み
- 公開解析済みのLevel-5 **V2 QR**アルゴリズムを再実装
- Type範囲からQRを1〜200枚生成
- Variationのランダム / 連番 / 固定生成
- QR画像のPNG保存
- 2143件のデータセットをgzip+base64で静的埋め込み（約48KB）
- 生成コード一覧のテキスト出力
- QR画像のドラッグ&ドロップ / ペースト解析
- V2 checksum検証
- 読み取ったTypeをJP Ver.4.0の`QR2_INFO`へ逆引き
- Flag付き / 2アイテム / RandomQRTable使用エントリの可視化
- 完全静的構成。サーバー・API・ビルド工程不要

## Dataset

対象:

- Region: Japan
- Game: Yo-kai Watch 3 Sukiyaki
- Game-facing version: Ver.4.0
- Source: `data/res/qr/qr_config_0.01r.cfg.bin`
- Source SHA-256: `971d3447f1dc49305f3bd4f72c6881fda02cface81d941fb082fcfbf15a8a134`
- `QR2_INFO`: 2,143 entries

ゲーム本体・CIA・RomFS・元`cfg.bin`はこのリポジトリには含めません。Webアプリに必要な解析済みメタデータのみを格納します。

## V2 QR format

```text
Type       3 base36 chars
Variation  4 base36 chars
Checksum  26 chars
----------------------
Code      33 chars
```

ブラウザ実装は起動時に既知のテストベクタを自己検証します。

```text
input: Q1B0000
code : Q1B00008CLTN07O0A2VJ3EU5L3LETAB3G
```

## Local preview

ビルド不要です。静的HTTPサーバーからリポジトリのルートを配信してください。

```bash
python -m http.server 8000
```

その後 `http://localhost:8000/` を開きます。

`file://` 直開きではブラウザの `fetch()` 制約でデータを読めない場合があります。

## GitHub Pages

`.github/workflows/pages.yml` を用意しています。

1. Repository Settings → Pages
2. Build and deployment → Source を **GitHub Actions**
3. `main` へpush、または `Deploy GitHub Pages` を手動実行

Private repositoryからのPages公開可否はGitHubプラン/組織設定に依存します。

## Structure

```text
.
├── index.html
├── assets/
│   ├── styles.css
│   └── favicon.svg
├── src/
│   ├── app.js
│   └── qr-v2.js
├── data/
│   ├── qr2-jp40.js
│   ├── item-names.json
│   └── metadata.json
├── tools/
│   ├── qr_v2.py
│   └── validate_dataset.py
└── docs/
    ├── DATA.md
    ├── SOURCES.md
    ├── UNMAPPED.md
    └── VALIDATION.md
```

## Important behavior

このツールは **JP Ver.4.0の既存QRエントリを選択してQRを生成**します。

QR文字列へ任意のItem IDを直接埋め込む仕組みではありません。ゲーム側の`QR2_INFO`に存在しない効果を、未改造のゲームへ自由に追加することはできません。

Flag付きエントリはゲーム状態へ影響する可能性があります。意味が未特定のFlagを含むQRを試す場合はセーブデータのバックアップを推奨します。

## Credits / references

解析方式・QR方式の確認には以下の公開資料を参照しています。

- YKW-Modding / yo-docs
- n123git / QRTool
- Kuriimu / Level-5 ARC0 implementation
- 公開YW3 Item ID tables

詳細は [`docs/SOURCES.md`](docs/SOURCES.md) を参照してください。

## Disclaimer

This is an independent research utility. It is not affiliated with LEVEL-5, Nintendo, or the Yo-kai Watch rights holders.

Code in this repository is MIT licensed. Game names, trademarks, and original game data belong to their respective owners.
