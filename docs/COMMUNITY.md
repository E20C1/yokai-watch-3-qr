# Community verified data

`YW3 QR Lab` keeps the extracted JP Ver.4.0 `QR2_INFO` table as the canonical raw layer and overlays human-readable reward names from `Yu08083/Yokai2-QR`.

## Verified source

- Repository: `Yu08083/Yokai2-QR`
- File: `yw3/catalog.json`
- Compared commit: `04d7c9783a66e7216ad020b1775417462b5b8a5d`
- Compared blob: `003a0a0588ca2ba2a4eb7243d1c80e753e139446`
- Upstream editor license: MIT

The upstream README states that the listed Yo-kai Watch 3 QR receiving contents were all checked by the author on real hardware.

## Machine comparison

The comparison is field-by-field, not a name-only comparison. The reward signature includes:

`Item1 / Item2 / Flag1 / Flag2 / internal values u1,u2 / quantities / RandomQRTable`

Result for the JP updated table:

- QR2_INFO rows: **2143 / 2143**
- Unique internal reward signatures: **371 / 371 exact**
- Covered Type values: **26503 / 26503 exact**
- Conflicts: **0**
- Community-only Types: **0**
- Local-only Types: **0**
- JP4.0 Item IDs named by the community catalog: **175 / 175**

The upstream UI exposes **179 user-facing receiving contents**. This is smaller than the 371 internal signatures because multiple internal QR states can resolve to the same visible receiving content.

See `docs/COMMUNITY_COMPARISON.md` and `data/community-comparison.json` for the generated comparison result.

## Usage in this app

The app uses the community catalog for Japanese reward labels and item names, while retaining the locally extracted QR2 table for Type lookup, flags, internal values, and research views. QR image assets from the upstream project are not copied.
