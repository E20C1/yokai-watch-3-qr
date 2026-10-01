# Sources and provenance

The project was constructed from independently extracted metadata plus public reverse-engineering references.

## Public references

- YKW-Modding / yo-docs  
  https://github.com/YKW-Modding/yo-docs
- Adding Custom QR Codes (YW2/YW3)  
  https://github.com/YKW-Modding/yo-docs/blob/main/modding-guides/general/create-qrs.md
- YW3 Item IDs  
  https://github.com/YKW-Modding/yo-docs/blob/main/modding-resources/item-ids/YW3ItemIDs.md
- n123git / QRTool  
  https://github.com/n123git/QRTool
- Kuriimu Level-5 ARC0 implementation  
  https://github.com/IcySon55/Kuriimu

## What is not distributed

This repository does not include:

- CIA files
- CXI/NCCH files
- RomFS images
- `yw_a.fa`
- original `qr_config*.cfg.bin`

Only the parsed fields needed for research and generation are committed.

## V2 generator

The browser implementation in `src/qr-v2.js` is an independent implementation of the documented/publicly implemented format:

1. `Type(3)` + `Variation(4)` is upper-case base36.
2. HMAC-MD5 is applied sequentially with the two known V2 keys.
3. The second round receives the lower-case hex digest of the first round.
4. The final 16-byte digest is encoded through the Level-5 5-bit character table to produce a 26-character checksum.

A known test vector is checked at page startup.
