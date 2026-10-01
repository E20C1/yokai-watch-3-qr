# Dataset notes

## JP Ver.4.0

The operational generator dataset is derived from:

```text
data/res/qr/qr_config_0.01r.cfg.bin
SHA-256 971d3447f1dc49305f3bd4f72c6881fda02cface81d941fb082fcfbf15a8a134
```

Parsed `QR2_INFO` count: **2,143**.

The web application stores each entry as:

| Field | Meaning |
|---|---|
| `index` | Parsed list index |
| `typeStart` / `typeEnd` | Base36 Type range |
| `start` / `end` | Decimal representation of the Type range |
| `item1` / `item2` | Item IDs |
| `flag1` / `flag2` | GlobalBitFlag IDs activated by the entry |
| `u1` / `u2` | Currently-unresolved small fields |
| `qty1` / `qty2` | Item quantities |
| `randomTable` | Random QR table selector |

### Observed counts

- `Item2 != 0`: 51
- `Flag1 != 0`: 195
- `Flag2 != 0`: 2
- `RandomQRTable != 0`: 51

## Item names

The raw QR table contains IDs, not friendly display names.

`data/item-names.json` is a separate annotation layer built from public YW3 Item ID references. Unknown IDs intentionally remain `Unknown item 0xXXXXXXXX`; the project does not guess names.

## Regional comparison data

EU English Ver.1.2 comparison data is maintained separately during research. The public generator dataset committed here is intentionally pinned to JP Sukiyaki Ver.4.0 so that generation behavior cannot silently change between regions.

## Static embedding

The 2,143-entry JSON dataset is gzip-compressed and base64-embedded in `data/qr2-jp40.js`. The browser uses `DecompressionStream` when available and falls back to pako. This keeps the Pages payload small while retaining all parsed fields.
